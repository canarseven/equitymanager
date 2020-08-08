function random_rgba() {
    var o = Math.round, r = Math.random, s = 255;
    return 'rgba(' + o(r() * s) + ',' + o(r() * s) + ',' + o(r() * s) + ', 1)';
}

function createDataSets(data) {
    let dataSets = [];
    for (let index in data.tickers) {
        let ticker = data.tickers[index];
        let thisYear = new Date().getFullYear();
        var vol = $.parseJSON('[' + data.annual_volatility + ']')[0];
        var ret = $.parseJSON('[' + data.annual_returns + ']')[0];
        let myData = {
            x: (vol[ticker][thisYear] * 100).toFixed(2),
            y: (ret[ticker][thisYear] * 100).toFixed(2)
        }
        let dataSet = {
            label: ticker,
            data: [myData],
            backgroundColor: random_rgba()
        }
        dataSets.push(dataSet);
    }

    // Add the Portfolios to the dataSet
    for (let i in data.portfolios) {
        let portfolio = data.portfolios[i];
        let myData = {
            x: (portfolio.risk * 100).toFixed(2),
            y: (portfolio.ret * 100).toFixed(2)
        }
        let dataSet = {
            label: portfolio.name,
            data: [myData],
            backgroundColor: random_rgba()
        }
        dataSets.push(dataSet);
    }

    return dataSets;
}

function createFrontier(data) {
    let dataSets = createDataSets(data);
    var ctx = document.getElementById('efficientFrontier').getContext('2d');
    var scatterChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: dataSets
        },
        options: {
            scales: {
                xAxes: [{
                    type: 'linear',
                    position: 'bottom',
                    scaleLabel: {
                        display: true,
                        labelString: 'Risk (in %)'
                    }
                }],
                yAxes: [{
                    type: 'linear',
                    position: 'bottom',
                    scaleLabel: {
                        display: true,
                        labelString: 'Return (in %)'
                    }
                }],
            }
        }
    });
}