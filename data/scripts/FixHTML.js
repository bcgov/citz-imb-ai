const fs = require("fs");
const path = require("path");
const cheerio = require("cheerio");

const fixHtmlFiles = (dir) => {
	const files = fs.readdirSync(dir);

	files.forEach((file) => {
		const filePath = path.join(dir, file);
		const stat = fs.statSync(filePath);

		if (stat.isDirectory()) {
			fixHtmlFiles(filePath);
		} else if (path.extname(file) === ".html") {
			fixHtml(filePath);
		}
	});
};

const fixHtml = (filePath) => {
	const htmlContent = fs.readFileSync(filePath, "utf8");
	const $ = cheerio.load(htmlContent);

	$("p").each(function () {
		const pElement = $(this);
		if (pElement.children("div").length > 0) {
			pElement.replaceWith($("<div>").html(pElement.html()));
		}
	});

	fs.writeFileSync(filePath, $.html());
	console.log(`Fixed: ${filePath}`);
};

const directoryPath = path.join(__dirname, "html");
fixHtmlFiles(directoryPath);
