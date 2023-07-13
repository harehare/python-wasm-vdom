const pyodideVersion = "v0.23.4";
const scriptElement = document.createElement("script");
scriptElement.src = `https://cdn.jsdelivr.net/pyodide/${pyodideVersion}/full/pyodide.js`;

const scriptPath = () => {
	const scriptTag = [...document.querySelectorAll("script")].filter(
		(s) => s.src.indexOf("python-wasm-vdom.js") != -1
	)[0];
	const scriptPath = scriptTag
		? scriptTag.src.startsWith("http")
			? new URL(scriptTag.src).pathname
			: scriptTag.src
		: "";

	return scriptPath.split("/").slice(0, -1).join("/");
};

scriptElement.addEventListener("load", () => {
	const textPython = [
		...document.querySelectorAll('script[type="text/python"]'),
	]
		.map((p) => p.textContent)
		.join("\n");
	const srcPython = [
		...document.querySelectorAll('script[type="text/python"]'),
	]
		.map((p) => p.getAttribute("src"))
		.filter((v) => !!v);

	const getFileName = (src) => {
		const pathName = src.startsWith("http") ? new URL(src).pathname : src;
		return pathName.split("/").slice(-1)[0].split(".")[0];
	};

	async function main() {
		const pyodide = await loadPyodide();
		await pyodide.runPythonAsync(`
		from pyodide.http import pyfetch
		response = await pyfetch("${scriptPath()}/vdom.py")
		with open("vdom.py", "wb") as f:
			f.write(await response.bytes())
	`);
		pyodide.pyimport("vdom");
		pyodide.runPython(textPython);
		await Promise.all(
			srcPython.map(async (src) => {
				await pyodide.runPythonAsync(`
				from pyodide.http import pyfetch
				response = await pyfetch("${src}")
				with open("${getFileName(src)}.py", "wb") as f:
					f.write(await response.bytes())
		    `);
			})
		);
		srcPython.forEach((src) => {
			pyodide.pyimport(getFileName(src));
		});
	}
	main();
});

document.head.appendChild(scriptElement);
