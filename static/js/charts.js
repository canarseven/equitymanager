function random_rgba() {
    var o = Math.round, r = Math.random, s = 255;
    return 'rgba(' + o(r() * s) + ',' + o(r() * s) + ',' + o(r() * s) + ', 1)';
}

function createDataSets(data) {
    let dataSets = [];
    for (let index in data.tickers) {
        let ticker = data.tickers[index];
        let thisYear = new Date().getFullYear();
        let myData = {
            x: (data.annual_volatility[ticker][thisYear] * 100).toFixed(2),
            y: (data.annual_returns[ticker][thisYear] * 100).toFixed(2)
        }
        let dataSet = {
            label: ticker,
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