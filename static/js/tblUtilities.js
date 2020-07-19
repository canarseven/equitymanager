function refreshTbls(tbls, data) {
    for (let i in tbls) {
        let myTbl = document.getElementById(tbls[i]);
        myTbl.innerHTML = "";
        let tHead = myTbl.createTHead();
        let row = tHead.insertRow();
        let th = document.createElement("th");
        th.innerText = data[i];
        row.appendChild(th);
        myTbl.createTBody();
    }
}