class StorageClient{
	constructor(user_id, endpoints){
		this.user_id = user_id;
		this.endpoints = endpoints;
	}

	store(path, data){ // TODO: handle errors
		let fetchs = this.endpoints.array().map((e) => 
			fetch(e + "/" + this.user_id + "/" + path,{
				method: "PUT",
				mode: "cors",
				headers: { "Content-Type": "text/plain" },
				body: data
			})
		);
		return Promise.race(fetchs);
	}
	
	remove(path){ // TODO: handle errors
		let fetchs = this.endpoints.array().map((e) => 
			fetch(e + "/" + this.user_id + "/" + path,{
				method: "DELETE",
				mode: "cors",
			})
		);
		return Promise.race(fetchs);
	}

	// TODO: ugly and too long
	load(path, early_return = 3){
		return new Promise((resolve, reject) => {
			let resolved = false;
			let returned = 0;
			let a = this.endpoints.array();
			let results = Object.create(null); // {} without prototype

			function onError(err){
				console.log(err);
				returned += 1;
				if(returned == a.length && !resolved){
					reject("all downloads failed for "+path);
				}
			}

			function onText(text){
				returned += 1;
				if(resolved) return;
				
				if(text in results) results[text] += 1;
				else results[text] = 1;

				if(returned == a.length){
					// find most common result and return it
					let best = undefined;
					let m = 0;
					for(var t in results){
						if(results[t] > m){
							m = results[t];
							best = t;
						}
					}
					resolved = true;
					resolve(best);
				}

				if(early_return && results[text] >= early_return){
					resolved = true;
					resolve(text);
				}
			}

			function onResponse(r){
				r.text().then(onText, onError);
			}
			for (let e of a){
				let f = fetch(e + "/" + this.user_id + "/" + path,{
					method: "GET",
					mode: "cors",
				});
				f.then(onResponse, onError);
			}
		});
	}
	
	// TODO: convert to async iterator to display first results while waiting for
	//       slow endpoints
	search(path = "", pattern = "%", limit = undefined, offset = undefined){
		if (path.length > 1 && path.charAt(path.length-1) != "/") path += "/";
		let query = path + "?";
		if (pattern !== undefined) query += "pattern="+encodeURIComponent(pattern) + "&";
		if (limit !== undefined) query += "limit=" +encodeURIComponent(limit) + "&";
		if (offset !== undefined) query += "offset=" +encodeURIComponent(limit) + "&";
		
		return new Promise((resolve, reject) => {
			let a = this.endpoints.array();
			console.log("apis:", a);
			let results = Object.create(null);
			let returned = 0;
			let resolved = false;

			function onResponse(r){
				r.text().then(onText, onError);
			}
			function onError(err){
				console.log(err);
				returned += 1;
				if(returned == a.length && !resolved){
					reject("all downloads failed for "+path);
				}
			}
			function onText(text){
				returned += 1;
				let doc = (new DOMParser()).parseFromString(text, "text/html");
				let links = doc.querySelectorAll("body ul a[href]");
				for(let l of links){
					results[l.innerHTML] = true;
				}
				if(returned == a.length){
					resolve(Array.from(Object.keys(results)).sort());
				}
			}

			for (let e of a){
				let f = fetch(e + "/" + this.user_id + "/" + query,{
					method: "GET",
					mode: "cors",
				});
				f.then(onResponse, onError);
			}
		});
	}
	async isEmpty(){
		return (await this.search("", "%", 1)).length == 0;
	}
}

class EncryptedStorageClient{
	constructor(user_id, encryption_key, storage){
		this.user_id = user_id;
		this.encryption_key = encryption_key;
		this.plain_storage = storage;
	}

	static async create(username, password, endpointlist){
		// derive user id from username
		const userid_length = 10;
		let username_hash = new Uint8Array(
			await crypto.subtle.digest("SHA-512", text2buf(username)));
		let user_id = buf2hex(username_hash.slice(0, 10));

		let storage = new StorageClient(user_id, endpointlist);

		// derive salt from user id
		let salt = await crypto.subtle.digest("SHA-512", hex2buf(user_id));
		
		// derive encryption key from salt and password
		let basekey = await crypto.subtle.importKey("raw", text2buf(password),
			{name: "PBKDF2"}, false, ["deriveKey"]);
		let Pbkdf2Params = {"name": "PBKDF2", "hash": "SHA-512",
				"salt": salt, "iterations": 100000};
		let encryption_key = await crypto.subtle.deriveKey(
			Pbkdf2Params, basekey, {"name": "AES-CTR", "length": 256},
			false, ["encrypt", "decrypt"]);
		return new EncryptedStorageClient(user_id, encryption_key, storage);
	}

	async encryptString(cleartext){
		let iv = randbuf(16);
		let algo = {name: "AES-CTR", counter: iv, length: 64};
		let cipherdata = await crypto.subtle.encrypt(
			algo, this.encryption_key, text2buf(cleartext)
		);
		return { "iv": buf2hex(iv), "data": buf2hex(cipherdata)};
	}

	async decryptString(cipherobj){
		let iv = hex2buf(cipherobj.iv);
		let data = hex2buf(cipherobj.data);
		let algo = { // AesCtrParams
			name: "AES-CTR", counter: iv, length: 64
		};

		let cleardata = await crypto.subtle.decrypt(
			algo, this.encryption_key, data);
		return  buf2text(cleardata);
	}

	async store(path, dict){
		let encdict = {};
		for(let k of Object.keys(dict)){
			encdict[k] = await this.encryptString(dict[k]);
		}
		return await this.plain_storage.store(path, JSON.stringify(encdict));
	}
	async load(path){
		let encdict = JSON.parse(await this.plain_storage.load(path));
		let dict = {};
		for(let k of Object.keys(encdict)){
			dict[k] = await this.decryptString(encdict[k]);
		}
		return dict;
	}

	remove(path){ // async
		return this.plain_storage.remove(path);
	}

	isEmpty(){
		return this.plain_storage.isEmpty();
	}
	search(path = "", pattern = "%", limit = undefined, offset = undefined){
		return this.plain_storage.search(path, pattern, limit, offset);
	}
}

class EndpointList{
	constructor(elem){
		this.elem = elem;
		this.manually_configured = false;
		let thisEndpointList = this;
		this.elem.addEventListener("change",
			() => { thisEndpointList.manually_configured = true;});
	}

	*iter(){
		for (let o of this.elem.querySelectorAll("option")){
			if(o.selected) yield o.value;
		}
	}
	array(){
		return Array.from(this.iter());
	}
	async select_preferred(username, n){
		let h = await crypto.subtle.digest("SHA-512", text2buf(username));
		await this.shuffle(h);
		let i = 0;
		for (let x of this.elem.querySelectorAll("option")){
			x.selected = i < n;
			i++;
		}
	}

	async shuffle(xorit){
		for(let x of this.elem.querySelectorAll("option")){
			let h = await crypto.subtle.digest("SHA-512", text2buf(x.value));
			let k = buf2hex(xorbufs(h, xorit));
			x.setAttribute("data-sortkey", k);
		}
		let arr = Array.from(this.elem.querySelectorAll("option"));
		arr.sort((a, b) => {
			a = a.getAttribute("data-sortkey");
			b = b.getAttribute("data-sortkey");
			return (a>b) - (a<b);
		});

		for(let x of arr){
			this.elem.appendChild(x); // moves x to the bottom
		}
	}
}
