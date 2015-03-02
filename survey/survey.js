/*
 * This script fetchs the page at <url> and outputs a
 * JSON representation of the results in the format:
 *   {
 *     "url": url,
 *     "status": "success"/"fail",
 *     "page": {
 *        "hash": <sha-1>
 *     },
 *     "resources": [{"url": url, "hash": <sha-1>}]
 *   }
 * The script optionally writes the final rendered
 * HTML to <output>/<page.hash>.html.
 *
 * XXX configurable output directory
 * XXX support pluggable hash functions
 */

function Page(hash, latency) {
	this.hash = hash;
	this.latency = latency;
}

function Resource(url, hash, size) {
	this.url = url;
	this.hash = hash;
	this.size = size;
}

function Result(url) {
	this.url = url;
	this.status = 'success';
	this.page = null;
	this.resources = [];
}

function sha1(data) {
	var hash = CryptoJS.SHA1(data);
	return hash.toString(CryptoJS.enc.hex);
}

// if we want to write the rendered page out for inpection later
const WRITE_FS = true;
if (WRITE_FS)
	var fs = require('fs');

var system = require('system');
if(system.args.length < 2) {
	console.log('Usage: slimerjs survey.js url');
	slimer.exit(1);
} else {
	var url = system.args[1];
	if(!phantom.injectJs('cryptojs/sha1.js')) {
		console.log('Unable to inject CryptoJS');
		slimer.exit(1);
	} else {
		var result = new Result(url);
		var page = require('webpage').create();
		page.captureContent = [ /.*/ ]; // everything
		page.onError = function(message, stack) {};
		page.onResourceReceived = function(response) {
			// XXX handle chunked responses
			if(response.stage === 'end') {
				var url = response.url;
				var hash = sha1(response.body);
				var size = response.bodySize;
				resource = new Resource(url, hash, size);
				result.resources.push(resource);
			}
		};

		function fail() {
			result.status = 'fail';
			result.resources = [];
			result.page = null;
			console.log(JSON.stringify(result));
			slimer.exit(1);
		}
		var startTime;
		function handler(status) {
			if(status !== 'success') {
				fail();
			} else {
				var hash = sha1(page.content);
				var endTime = new Date();
				var latency = endTime - startTime;
				result.page = new Page(hash, latency);
				if (WRITE_FS) {
					var out = 'pages/'+hash+'.html';
					fs.write(out, page.content, 'w');
				}
				page.close();
				console.log(JSON.stringify(result));
				slimer.exit(0);
			}
		}
		window.setTimeout(fail, 30000);
		page.onLoadStarted = function() {
			startTime = new Date();
		}
		page.open(url, handler);
	}
}
