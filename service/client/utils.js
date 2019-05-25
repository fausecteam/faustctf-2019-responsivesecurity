const buf2hex = (buffer) => Array.prototype.map.call(new Uint8Array(buffer), x => ('00' + x.toString(16)).slice(-2)).join('');
const hex2buf = (hex) => new Uint8Array(hex?hex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)):[]);
const text2buf = (text) => (new TextEncoder("utf-8")).encode(text);
const buf2text = (buf) => (new TextDecoder("utf-8", {"fatal": true})).decode(buf);

const randbuf = (n) => crypto.getRandomValues(new Uint8Array(n));


function xorbufs(a, b){
	a = new Uint8Array(a);
	b = new Uint8Array(b);
	const n = Math.max(a.length, b.length);
	let c = new Uint8Array(n);
	for(let i=0; i<n; i++){
		c[i] = a[i % a.length] ^ b[i % b.length];
	}
	return c;
}

function mkElem(tag, attribs = {}, children = []){
	let elem = document.createElement(tag);
	for (let a in attribs) if(attribs.hasOwnProperty(a)){
		elem.setAttribute(a, attribs[a]);
	}
	for(let c of children){
		elem.appendChild(c);
	}
	return elem;
}


function cpElem(src){
	return src.cloneNode(true);
}

function rmElem(elem){
	elem.parentNode.removeChild(elem);
}


function read_form(form){
	res = {};
	for(var elem of form.querySelectorAll("input[name], textarea[name], select[name], [contenteditable=true][name]")){
		let k = elem.getAttribute("name");
		let v = undefined;
		if(elem.getAttribute("contenteditable") == "true") v= elem.innerHTML;
		else if(elem.getAttribute("type") == "checkbox") v = elem.checked;
		else v = elem.value;
		res[k] = v;
	}
	return res;
}

function query_form(form){
	return new Promise((resolve, reject) => {
		function onsubmit(e){
			form.style.display = "none";
			form.removeEventListener("submit", onsubmit);
			res = read_form(form);
			resolve(res);
			e.preventDefault();
			return false;
		}
		form.addEventListener("submit", onsubmit);
		form.style.display = "block";
	});
}

function sleep(ms){
	return new Promise((resolve, reject) => {
		window.setTimeout(resolve, ms);
	});
}
