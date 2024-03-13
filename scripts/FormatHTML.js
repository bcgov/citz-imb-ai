const { exec } = require("child_process");
const path = require("path");

const FormatHTML = (dir) => {
	const command = `npx prettier --write --print-width 80 --tab-width 2 --use-tabs false --trailing-comma all --single-quote true --end-of-line lf --bracket-spacing true --arrow-parens always --html-whitespace-sensitivity css --html-self-closing html "${dir}"`;

	exec(command, (error, stdout, stderr) => {
		if (error) {
			console.error(`exec error: ${error}`);
			return;
		}
		console.log(`stdout: ${stdout}`);
		console.error(`stderr: ${stderr}`);
	});
};

const directoryPath = path.join(__dirname, "html");
FormatHTML(directoryPath);
