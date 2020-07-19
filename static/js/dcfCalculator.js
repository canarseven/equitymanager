function dcfCalcForm() {
    $("#dcfCalcForm").submit(function (event) {
        let tbls = ["tblUFCF"];
        let headers = ["in MM USD"];
        event.preventDefault(); //prevent default action
        $("#submitBtn").prop("disabled", true);
        refreshTbls(tbls, headers);
        let post_url = $(this).attr("action"); //get form action url
        let request_method = $(this).attr("method"); //get form GET/POST method
        let form_data = $(this).serialize(); //Encode form elements for submission
        addLoading(tbls[0]);
        //addLoading(tbls[1]);

        $.ajax({
            url: post_url,
            type: request_method,
            data: form_data,
            success: function (data) {
                removeLoading();
                createDCFTable(tbls[0], data);
                //createDCFTable(tbls[1], "pps", data);
                //createFrontier(data);
                $("#submitBtn").prop("disabled", false);
            }
        });
        return false;
    });
}

function formatNumber(num) {
    return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
}

function buildDCFTblHead(tblId, data) {
    let tHead = document.getElementById(tblId).getElementsByTagName("thead")[0];
    let row = tHead.children[0];
    for (let i in data) {
        let cell = document.createElement("th");
        let text = document.createTextNode(data[i]);
        cell.appendChild(text);
        row.appendChild(cell);
    }
}

function buildUFCFTblBody(tblId, data) {
    let tBody = document.getElementById(tblId).getElementsByTagName("tbody")[0];
    let dataSet = data.ufcf;
    for (let param in dataSet) {
        if (param === "used_params") {
            for (let used_param in dataSet[param]) {
                let row = tBody.insertRow();
                let cell = row.insertCell();
                let myParamValues = dataSet[param][used_param];
                let bold = document.createElement('strong');
                let text = document.createTextNode(used_param);
                bold.appendChild(text);
                cell.appendChild(bold);
                for (let index in myParamValues) {
                    cell = row.insertCell(1);
                    let dataNum = myParamValues[index] / 1000000;
                    text = document.createTextNode(formatNumber(dataNum));
                    cell.appendChild(text);
                }
            }
        } else {
            let row = tBody.insertRow();
            let cell = row.insertCell();
            let bold = document.createElement('strong');
            let text = document.createTextNode("UFCF");
            bold.appendChild(text);
            cell.appendChild(bold);
            for (let index in dataSet[param]) {
                cell = row.insertCell();
                let ufcf = dataSet[param][index] / 1000000;
                bold = document.createElement('strong');
                text = document.createTextNode(formatNumber(ufcf));
                bold.appendChild(text);
                cell.appendChild(bold);
            }
        }
    }
}

function createDCFTable(tblId, data) {
    buildDCFTblHead(tblId, data.years);
    buildUFCFTblBody(tblId, data);
}