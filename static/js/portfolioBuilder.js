function pBuilderForm() {
    $("#pBuilderForm").submit(function (event) {
        let tbls = ["tblReturns", "tblVolats"];
        let headers = ["Calculated Returns", "Calculated Volatility"];
        event.preventDefault(); //prevent default action
        $("#submitBtn").prop("disabled", true);
        refreshTbls(tbls, headers);
        let post_url = $(this).attr("action"); //get form action url
        let request_method = $(this).attr("method"); //get form GET/POST method
        let form_data = $(this).serialize(); //Encode form elements for submission
        addLoading(tbls[0]);
        addLoading(tbls[1]);

        $.ajax({
            url: post_url,
            type: request_method,
            data: form_data,
            success: function (data) {
                removeLoading();
                createPBuilderTable(tbls[0], "return", data);
                createPBuilderTable(tbls[1], "risk", data);
                createFrontier(data);
                $("#submitBtn").prop("disabled", false);
            }
        });
        return false;
    });
}

function buildTblHead(tblId, data) {
    let tHead = document.getElementById(tblId).getElementsByTagName("thead")[0];
    let row = tHead.children[0];
    for (let i in data) {
        let cell = document.createElement("th");
        let text = document.createTextNode(data[i]);
        cell.appendChild(text);
        row.appendChild(cell);
    }
}

function buildTblBody(tblId, type, data) {
    let tBody = document.getElementById(tblId).getElementsByTagName("tbody")[0];
    let dataSet = data.annual_returns;
    if (type === "risk") {
        dataSet = data.annual_volatility;
    }
    for (let ticker in dataSet) {
        let row = tBody.insertRow();
        let cell = row.insertCell();
        let text = document.createTextNode(ticker);
        cell.appendChild(text);
        for (let year in dataSet[ticker]) {
            cell = row.insertCell(1);
            let dataNum = dataSet[ticker][year] * 100;
            text = document.createTextNode(dataNum.toFixed(2));
            cell.appendChild(text);
        }
    }
}

function createPBuilderTable(tblId, type, data) {
    buildTblHead(tblId, data.years);
    buildTblBody(tblId, type, data);
}