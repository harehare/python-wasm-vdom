# python-wasm-vdom

This repository is inspired by [getty104/ruby-wasm-vdom](https://github.com/getty104/ruby-wasm-vdom).

A virtual dom library in python using wasm.

It is lightweight and has few functions, so it is suitable for creating trial pages.

## How to use

```python
<html>
	<head />
	<body>
		<div id="app">Loading...</div>
		<script src="python-wasm-vdom.js"></script>
		<script type="text/python">
			from vdom import App, p

			state = {
			  'count': 0,
			}

			def increment(state, value):
			    state['count'] += 1

			actions = {
			  'increment': increment
			}

			def view(state, actions):
			  return p('div', {}, [
			    p('button', { 'onClick': lambda e: actions['increment'](state, None) }, ['Click me!']),
			        p('p', {}, [f"Count is {state['count']}"])
			    ])

			App(
			  selector='#app',
			  state=state,
			  view=view,
			  actions=actions,
			)
		</script>
	</body>
</html>
```

```html
<html>
	<head />
	<body>
		<div id="app">Loading...</div>
		<script src="python-wasm-vdom.js"></script>
		<script type="text/python" src="counter.py"></script>
	</body>
</html>
```
