function autocomplete(inp, arr) {
    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    var currentFocus;
    /* a list that stores all entered equities*/
    var allEquities = {};
    /*execute a function when someone writes in the text field:*/
    inp.addEventListener("input", function (e) {
        var a, b, i, val = this.value;
        /*close any already open lists of autocompleted values*/
        closeAllLists();
        if (!val) {
            return false;
        }
        currentFocus = -1;
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        /*append the DIV element as a child of the autocomplete container:*/
        this.parentNode.appendChild(a);
        /*for each item in the array...*/
        for (i = 0; i < arr.length; i++) {
            /*check if the item starts with the same letters as the text field value:*/
            if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
                /*create a DIV element for each matching element:*/
                b = document.createElement("DIV");
                /*make the matching letters bold:*/
                b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
                b.innerHTML += arr[i].substr(val.length);
                /*insert a input field that will hold the current array item's value:*/
                b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
                /*execute a function when someone clicks on the item value (DIV element):*/
                b.addEventListener("click", function (e) {
                    /*insert the value for the autocomplete text field:*/
                    inp.value = this.getElementsByTagName("input")[0].value;
                    /*close the list of autocompleted values,
                    (or any other open lists of autocompleted values:*/
                    closeAllLists();
                    if (!(inp.value in allEquities)) {
                        allEquities[inp.value] = inp.value;
                        addDiv(inp.value, allEquities);
                        inp.value = "";
                    }
                });
                a.appendChild(b);
            }
        }
    });
    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function (e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            /*If the arrow DOWN key is pressed,
            increase the currentFocus variable:*/
            currentFocus++;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 38) { //up
            /*If the arrow UP key is pressed,
            decrease the currentFocus variable:*/
            currentFocus--;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 13) {
            /*If the ENTER key is pressed, prevent the form from being submitted,*/
            e.preventDefault();
            if (currentFocus > -1) {
                /*and simulate a click on the "active" item:*/
                if (x) x[currentFocus].click();
            }
        }
    });

    function addActive(x) {
        /*a function to classify an item as "active":*/
        if (!x) return false;
        /*start by removing the "active" class on all items:*/
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        /*add class "autocomplete-active":*/
        x[currentFocus].classList.add("autocomplete-active");
    }

    function removeActive(x) {
        /*a function to remove the "active" class from all autocomplete items:*/
        for (var i = 0; i < x.length; i++) {
            x[i].classList.remove("autocomplete-active");
        }
    }

    function closeAllLists(elmnt) {
        /*close all autocomplete lists in the document,
        except the one passed as an argument:*/
        var x = document.getElementsByClassName("autocomplete-items");
        for (var i = 0; i < x.length; i++) {
            if (elmnt != x[i] && elmnt != inp) {
                x[i].parentNode.removeChild(x[i]);
            }
        }
    }

    /*execute a function when someone clicks in the document:*/
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
}

function addDiv(text, myJson) {
    // create a new div element
    let newDiv = document.createElement("div");
    // and give it some content
    newDiv.name = text;
    newDiv.className = "chosen-equity";
    newDiv.onmouseover = () => {
        newDiv.classList.add("hover");
    };
    newDiv.onmouseleave = () => {
        newDiv.classList.remove("hover");
    };
    let newContent = document.createTextNode(text);
    // add the text node to the newly created div
    newDiv.appendChild(newContent);

    // add the newly created element and its content into the DOM
    let currentDiv = document.getElementById("equities");
    currentDiv.appendChild(newDiv);
    newDiv.onclick = () => {
        delDiv(text, myJson)
    };

    //add hidden input field for ajax request later
    addHidden(text);
}

function addHidden(text) {
    let hiddenInput = document.getElementById("chosenTickers");
    let inputJson = {};
    if (hiddenInput.value) {
        inputJson = JSON.parse(hiddenInput.value);
    }
    inputJson[text] = text;
    hiddenInput.value = JSON.stringify(inputJson);
}

function delHidden(text) {
    let hiddenInput = document.getElementById("chosenTickers");
    let inputJson = JSON.parse(hiddenInput.value);
    delete inputJson[text];
    hiddenInput.value = JSON.stringify(inputJson);
}

function delDiv(text, myJson) {
    removeChildren(text, "equities");
    delHidden(text);
    delete myJson[text];
}

function removeChildren(removeMe, parentId) {
    let childNodes = document.getElementById(parentId).childNodes;
    for (let i = childNodes.length - 1; i >= 0; i--) {
        let childNode = childNodes[i];
        if (childNode.name == removeMe) {
            childNode.parentNode.removeChild(childNode);
        }
    }
}