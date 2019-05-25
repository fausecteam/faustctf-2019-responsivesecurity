function randomize_select(elem){
	var o = elem.options;
	var i = Math.floor(Math.random() * o.length);
	o[i].selected = true;
}

gCharacterClass = {}

function initCharacterClasses(){
	let classes = [" abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "!,.:;?-_", "01234567890", "äöüÄÖÜßẞ", "şčŞČ", "æœå", "@#%^&$", "+*/\\|()[]{}<>"];
	for(cc of classes){
		for(c of cc){
			gCharacterClass[c] = cc;
		}
	}
}

function characterQuality(password){
	var used_classes = {};
	for(c of password){
		used_classes[gCharacterClass[c] || "unknown"] = true;
	}
	var s = 0;
	for(uc in used_classes){
		s += uc.length;
	}
	return Math.log(s)/Math.log(2);
}

function evaluate_password(input, output, submit){
	var password = input.value;

	if(!output.firstChild){
		output.appendChild(document.createElement("span"));
		output.appendChild(document.createTextNode(" "));
		output.appendChild(document.createElement("span"));
	}

	var scoreOut = output.firstChild;
	var breachOut = scoreOut.nextSibling.nextSibling;

	var c = characterQuality(password);
	var n = password.length;
	
	var q = n ? c*n : 0;
	
	scoreOut.textContent = Math.floor(q);
	breachOut.style.display = "inline";
	breachOut.innerHTML = "querying";
	submit.disabled = true;

	check_breach(password).then(function(breach){
		if(input.value != password) return;

		submit.disabled = breach;
		breachOut.style.display = breach ? "inline" : "none";
		breachOut.setAttribute("class", "breached");
		if(breach) breachOut.innerHTML = "known insecure!"
	});
}

async function check_breach(password){
	let data = new TextEncoder().encode(password);
	let hash = buf2hex(await crypto.subtle.digest("SHA-1", data)).toUpperCase();
	let prefix = hash.substr(0, 5);
	let suffix = hash.substr(5);
	let success = false;
	do{
		let endpoint = document.getElementById("config").pwned_endpoint.value;
		try{
			var response = await((await fetch(endpoint + "/range/" + prefix)).text())
			success = true;
		}
		catch(err){
			console.log(err);
			console.log("randomizing");
			randomize_select(document.getElementById("config").pwned_endpoint);
		}
	} while(!success);
	return response.indexOf(suffix) != -1;
}

function bind_pw_checker(input, output){
	var f = output;
	while(f && f.tagName != "FORM") f = f.parentNode;
	if(!f) {
		console.log("form not found!");
		return;
	}
	submit = f.querySelector("input[type=submit]");
	if(!submit){
		console.log("submit not found!");
		return;
	}
	input.addEventListener("input", (evt) => evaluate_password(input, output, submit));
}

function init(){
	initCharacterClasses();
	

	for(output of document.getElementsByClassName("password-evaluation")){
		let pwid = output.getAttribute("for").split(" ")[0];
		if(!pwid) continue;
		let input = document.getElementById(pwid);
		if(!input) continue;
		bind_pw_checker(input, output);
	}
}

window.addEventListener("load", init);
