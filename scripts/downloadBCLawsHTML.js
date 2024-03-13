const axios = require("axios");
const cheerio = require("cheerio");
const fs = require("fs-extra");
const path = require("path");

const BASE_URL = "https://www.bclaws.gov.bc.ca/civix/content/complete/statreg/";

async function fetchContent(url) {
	try {
		const response = await axios.get(url);
		return cheerio.load(response.data);
	} catch (error) {
		console.error(`Error fetching URL ${url}:`, error.message);
		return null;
	}
}

async function downloadXML(url, filename) {
	try {
		const response = await axios.get(url, { responseType: "stream" });
		await fs.ensureDir(path.dirname(filename));
		const writer = fs.createWriteStream(filename);
		response.data.pipe(writer);
		return new Promise((resolve, reject) => {
			writer.on("finish", resolve);
			writer.on("error", reject);
		});
	} catch (error) {
		console.error(`Error downloading file ${url}:`, error.message);
	}
}

async function processDirectory(url, depth = 0) {
	const $ = await fetchContent(url);
	if (!$) return;

	const dirs = $("dir").toArray();
	for (let elem of dirs) {
		const documentStatus = $(elem).find("CIVIX_DOCUMENT_STATUS").text();
		if (documentStatus === "Repealed") continue;

		const documentId = $(elem).find("CIVIX_DOCUMENT_ID").text();
		if (!documentId) continue;

		const nextUrl = `${BASE_URL}${"/".repeat(depth)}${documentId}`;
		await processDirectory(nextUrl, depth + 1);
	}

	const documents = $("document").toArray();
	for (let elem of documents) {
		const documentId = $(elem).find("CIVIX_DOCUMENT_ID").text();
		const documentTitle = $(elem).find("CIVIX_DOCUMENT_TITLE").text();
		const documentExt = $(elem).find("CIVIX_DOCUMENT_EXT").text();
		let downloadUrl;

		if (documentExt === "htm") {
			downloadUrl = `https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/${documentId}_multi`;
		} else if (documentExt === "xml") {
			downloadUrl = `https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/${documentId}`;
		}

		if (downloadUrl) {
			const sanitizedTitle = documentTitle
				.replace(/[^a-zA-Z0-9\s]/g, "")
				.replace(/\s+/g, "_");
			const filename = path.join(
				__dirname,
				"downloads",
				`${sanitizedTitle}.${documentExt === "htm" ? "multi.html" : "html"}`
			);
			await downloadXML(downloadUrl, filename);
		}
	}
}

processDirectory(BASE_URL).then(() => console.log("Download completed."));
