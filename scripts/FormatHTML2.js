const { spawn } = require("child_process");
const path = require("path");

const FormatHTML = (dir) => {
	const args = [
		"--write",
		"--print-width",
		"80",
		"--tab-width",
		"2",
		"--use-tabs",
		"false",
		"--trailing-comma",
		"all",
		"--single-quote",
		"true",
		"--end-of-line",
		"lf",
		"--bracket-spacing",
		"true",
		"--arrow-parens",
		"always",
		"--html-whitespace-sensitivity",
		"css",
		"--html-self-closing",
		"html",
		`${dir}/**/*.html`,
	];

	const prettier = spawn("npx", ["prettier", ...args]);

	prettier.stdout.on("data", (data) => {
		console.log(`stdout: ${data}`);
	});

	prettier.stderr.on("data", (data) => {
		console.error(`stderr: ${data}`);
	});

	prettier.on("close", (code) => {
		console.log(`child process exited with code ${code}`);
	});
};

const directoryPath = path.join(__dirname);
FormatHTML(directoryPath);
