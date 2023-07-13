const pyodideVersion = "v0.23.4";
const scriptElement = document.createElement("script");
scriptElement.src = `https://cdn.jsdelivr.net/pyodide/${pyodideVersion}/full/pyodide.js`;

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
		response = await pyfetch("vdom.py")
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
