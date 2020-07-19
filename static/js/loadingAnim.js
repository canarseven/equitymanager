function addLoading(elemId) {
    let loaderDiv = document.createElement("div");
    loaderDiv.className = "loader";
    loaderDiv.tagName = "loadAnim";
    let elem = document.getElementById(elemId);
    let tr = elem.tHead.children[0];
    let th = document.createElement("th");
    th.appendChild(loaderDiv);
    tr.appendChild(th);
}

function removeLoading() {
    let elem = document.getElementsByClassName("loader");
    let len = elem.length;
    for (let i = 0; i < len; i++) {
        let grandParentNode = elem[0].parentNode.parentNode;
        let removeMe = grandParentNode.children[1];
        grandParentNode.removeChild(removeMe);
    }

}