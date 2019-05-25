
class Row{
	constructor(manager, site = "", username = "", password = "", notes = "", id = undefined){
		this.id = id;
		if(id === undefined){
			this.id = buf2hex(randbuf(20));
		}
		this.manager = manager;
		
		// html skeleton
		this.elem = document.getElementById("row-template").content.firstElementChild.cloneNode(true);
		this.manager.table.appendChild(this.elem);

		this.site_input = this.elem.querySelector('[name="site"]');
		this.username_input = this.elem.querySelector('[name="username"]');
		this.password_input = this.elem.querySelector('[name="password"]');
		this.notes_span = this.elem.querySelector('[name="notes"]');
		
		// fill page through accessors
		this.password = password;
		this.site = site;
		this.username = username;
		this.notes = notes;
		
		// setup buttons and events
		let thisRow = this;
		this.elem.addEventListener("submit", (e) => {
			thisRow.save().then(() => fadeMsg("saved", "alert-success"), ()=>fadeMsg("error saving, -> console", "alert-warning"));
			e.preventDefault();
			return false;
		});
		this.elem.querySelector("input.delete").addEventListener("click", (e) => {
			thisRow.remove().catch((e) => { console.log(e); fadeMsg("error deleting", "alert-warning"); });
		});
		this.elem.setAttribute("data-rowid", this.id);
		//this.notes_span.parentNode.addEventListener("click", (ev) => (ev.target.firstElementChild.focus()));
		this.notes_span.addEventListener("input", (ev) => {
			console.log("input", ev.target.innerHTML);
			if(ev.target.innerHTML == "") ev.target.innerHTML="&nbsp;";});
		this.elem.querySelector(".pwvisible").addEventListener("click", (ev) =>
			thisRow.password_input.setAttribute("type", thisRow.password_input.getAttribute("type") == "password" ? "text" : "password"))
		
	}

	get site(){ return this.site_input.value; }
	get notes(){ return this.notes_span.innerHTML; }
	get username(){ return this.username_input.value; }
	get password(){ return this.password_input.value; }

	set site(val){ this.site_input.value = val; }
	set notes(val){ this.notes_span.innerHTML = val; }
	set username(val){ this.username_input.value = val; }
	set password(val){ this.password_input.value = val; }

	async save(){
		let obj = {
			site: this.site,
			username: this.username,
			password: this.password,
			notes: this.notes
		}
		await this.manager.storage.store("p/" + this.id, obj);
	}

	async remove(){
		await this.manager.storage.remove("p/" + this.id);
		rmElem(this.elem);
	}
}

class PasswordManager{
	constructor(storage, elem){
		this.storage = storage;
		this.elem = elem;
		this.table = this.elem.querySelector(".table");
		let newbutton = mkElem("input", {"type": "button", "value": "New Entry"}, []);
		this.elem.appendChild(newbutton);
		let thisPasswordManager = this;
		newbutton.addEventListener("click", (e)=>{thisPasswordManager.newRow()});
	}
	async demo(){
		let row = new Row(this, "example.org", "me", "yachaeS4wo5F", "In this area you can store notes like<ul><li>the email address used for the account</li><li>direct links to special subpages, like <a href=\"https://exmaple.org/account_settings\">Preferences</a></li><li>TANs or Flags</li><li>other data you want to keep safe</li></ul> If you focus this area, formatting tools should appear");
		await row.save();

	}
	
	async newRow(){
		new Row(this, "", "", "", "&nbsp;");
		// dont save
	}

	async load(id){
		let obj = await this.storage.load("p/"+id);
		let row = new Row(this, obj.site, obj.username, obj.password, obj.notes, id);
	}

	async show_all(id){
		// clear
		for(let x of this.table.querySelectorAll(".pw-row")){
			rmElem(x);
		}

		for(let id of await this.storage.search("p/")){
			id = id.substr(2);
			console.log("result id", id);
			await this.load(id);
			console.log("loaded");
		}
	}
}

function fadeMsg(text, classes){
	let elem = null;
	document.getElementById("messages-bottom").appendChild(
		elem=mkElem("div", {"class": "alert " + (classes?classes:"")}, [document.createTextNode(text)])
	);
	window.setTimeout(()=>{rmElem(elem)}, 2000);
}


async function query_use_empty_api(){
	return confirm("Opened empty database. Use it?\nIf you didn't want to create a new account, your password or endpoint selection is wrong.");
}

function fill_endpoint_list(){
	let storage = document.getElementById("config").storage_endpoints;
	for(let x of storage.querySelectorAll("option")) rmElem(x);
	let pwned = document.getElementById("config").pwned_endpoint;
	for(let x of pwned.querySelectorAll("option")) rmElem(x);
	

	function add(root, name){
		storage.appendChild(mkElem("option", {"value": root+"storage"}, [document.createTextNode(name)]));
		pwned.appendChild(mkElem("option", {"value": root+"pwned"}, [document.createTextNode(name)]));
	}

	if(window.location.hostname == "10.66.254.2" || window.location.hostname == "vulnbox-test.faust.ninja"){
		add(window.location.origin + "/responsivesecurity/", "testvulnboxt");
	}
	else{
		// ctf network
		for(let teamid=1; teamid<=255; teamid++){
			let name = teamid == 1 ? "NOP-Team" : ("Team " + (teamid));
			let root = "http://10.66." + (teamid) + ".2:5002/responsivesecurity/";
			add(root, name);
		}
	}
}

async function init_responisivesecurity(){
	fill_endpoint_list();
	randomize_select(document.getElementById("config").pwned_endpoint);

	var logged_in = false;
	while(!logged_in){
		let x = await query_form(document.getElementById("keygen_form"));
		let username = x["account_username"];
		let password = x["account_password"];
		if(x["create_account"]) if(x["confirm_password"] != x["account_password"]){
			fadeMsg("passwords do not match", "alert-warning");
			continue;
		}

		let endpoints = new EndpointList(document.getElementById("config").storage_endpoints);
		if(!endpoints.manually_configured) await endpoints.select_preferred(username, 10);

		console.log("endpoints selected");

		var api = await EncryptedStorageClient.create(username, password, endpoints);
		console.log("api created");
		var account_empty = await api.isEmpty();
	
		console.log("api queried - empty:", account_empty);


		if(x["create_account"]){
			if(account_empty) logged_in = true;
			else fadeMsg("user already exists.", "alert-warning");
		}
		else if(account_empty){
			fadeMsg("user does not exist. Check \"Create new\" to create it.", "alert-warning");
		}
		else {
			try{
				await api.load("pwcheck/checkobj");
				logged_in = true;
			}
			catch(err){
				console.log(err);
				fadeMsg("error - invalid password?", "alert-warning");
			}
		}
	}

	if(account_empty){
		teststr = buf2hex(randbuf(20));
		await api.store("pwcheck/checkobj", {"something":teststr});
	}

	password_list = new PasswordManager(api, document.getElementById("manager"));
	password_list.elem.style.display="block";

	if(account_empty) {
		await password_list.demo();
	}

	await password_list.show_all("", 20);
}

window.addEventListener("load", init_responisivesecurity);
