# pylint: disable=E0401
import js
import functools
from pyodide.ffi import create_once_callable, create_proxy
from enum import Enum
from typing import Callable, TypedDict, Sequence, MutableMapping, Union


State = MutableMapping[str, Union[str, int, dict, list, None]]
Actions = dict[str, Callable]

Attributes = dict[str, Union[str, int, tuple[str]]]


class VDom(TypedDict):
    node_name: str
    attributes: Attributes
    children: Sequence[Union[str, "VDom"]]


def p(
    node_name: str, attributes: Attributes, children: Sequence[Union[str, "VDom"]]
) -> VDom:
    if not isinstance(children, Sequence):
        return {
            "node_name": node_name,
            "attributes": attributes,
            "children": [children],
        }

    return {"node_name": node_name, "attributes": attributes, "children": children}


class App:
    def __init__(
        self,
        selector: str,
        state: State,
        view: Callable[[State, Actions], VDom],
        actions: Actions,
    ):
        def dispatch_action(action, state, data):
            action(state, data)
            self.resolve_node()

        self.view = view
        self.state = state
        self.actions = {
            name: functools.partial(dispatch_action, action)
            for name, action in actions.items()
        }
        self.skip_render = False
        self.new_node = None
        self.current_node = None
        self.dom_manager = DomManager(selector)
        self.resolve_node()

    def resolve_node(self):
        self.new_node = self.view(self.state, self.actions)
        self.schedule_render()

    def render(self, _):
        self.dom_manager.render(self.new_node)
        self.skip_render = False

    def schedule_render(self):
        if not self.skip_render:
            self.skip_render = True

        js.requestAnimationFrame(create_once_callable(self.render))


class DomManager:
    def __init__(self, selector: str) -> None:
        self.element = js.document.querySelector(selector)
        self.element.innerHTML = ""
        self.v_current_node = None

    class ChangeType(Enum):
        NONE = 1
        TYPE = 2
        TEXT = 3
        NODE = 4
        VALUE = 5
        ATTR = 6

    def render(self, v_new_node):
        if self.v_current_node:
            self.update_element(self.element, self.v_current_node, v_new_node)
        else:
            self.element.appendChild(self.create_element(v_new_node))

        self.v_current_node = v_new_node

    def create_element(self, v_node):
        if not self.is_v_node(v_node):
            return js.document.createTextNode(str(v_node))

        element = js.document.createElement(v_node["node_name"])
        self.set_attributes(element, v_node["attributes"])

        for child in v_node["children"]:
            element.appendChild(self.create_element(child))

        return element

    def set_attributes(self, element, attributes):
        for attr, value in attributes.items():
            if self.is_event_attr(attr):
                element.addEventListener(attr[2:].lower(), create_proxy(value))
            else:
                element.setAttribute(str(attr), value)

    def update_element(
        self, parent_node, v_current_node, v_new_node, current_node_index=0
    ):
        if not v_current_node:
            parent_node.appendChild(self.create_element(v_new_node))
            return

        current_node = (
            parent_node.childNodes[current_node_index]
            if len(parent_node.childNodes) > current_node_index
            else parent_node.childNodes[-1]
        )

        if not v_new_node:
            parent_node.removeChild(current_node)
            return

        change_type = self.change_type(v_current_node, v_new_node)

        if change_type in [
            self.ChangeType.TYPE,
            self.ChangeType.TEXT,
            self.ChangeType.NODE,
        ]:
            parent_node.replaceChild(self.create_element(v_new_node), current_node)

        if change_type == self.ChangeType.VALUE:
            current_node.value = v_new_node["attributes"].get("value")

        if change_type == self.ChangeType.ATTR:
            self.update_attributes(
                current_node, v_current_node["attributes"], v_new_node["attributes"]
            )

        if not self.is_v_node(v_current_node) or not self.is_v_node(v_new_node):
            return

        for i in range(
            max([len(v_current_node["children"]), len(v_new_node["children"])])
        ):
            v_current_node_child = (
                v_current_node["children"][i]
                if i < len(v_current_node["children"])
                else None
            )
            v_new_node_child = (
                v_new_node["children"][i] if i < len(v_new_node["children"]) else None
            )

            self.update_element(current_node, v_current_node_child, v_new_node_child, i)

    def update_attributes(self, target_node, current_attributes, new_attributes):
        for attr in list(set(current_attributes.keys()) - set(new_attributes)):
            if self.is_event_attr(str(attr)):
                continue
            target_node.removeAttribute(str(attr))

        for attr, value in new_attributes.items():
            if (
                self.is_event_attr(str(attr))
                or current_attributes.get(str(attr)) == value
            ):
                continue
            target_node.setAttribute(str(attr), value)

    def change_type(self, a, b):
        if a.__class__.__name__ != b.__class__.__name__:
            return self.ChangeType.TYPE

        if not self.is_v_node(a) and a != b:
            return self.ChangeType.TEXT

        if self.is_v_node(a) and self.is_v_node(b):
            if a["node_name"] != b["node_name"]:
                return self.ChangeType.NODE

            if a["attributes"].get("value") != b["attributes"].get("value"):
                return self.ChangeType.VALUE

            if a["attributes"] != b["attributes"]:
                return self.ChangeType.ATTR

        return self.ChangeType.NONE

    def is_v_node(self, node):
        return isinstance(node, dict)

    def is_event_attr(self, attr: str):
        return attr.startswith("on")
