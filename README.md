# equitymanager
One of my personal projects that uses Django to provide automatic equity management. I am using financialmodelingprep.com
as the API to obtain fundamental data. The three main functions of this project are:

* Equity Financial Analysis
* Portfolio Construction
* Trading

Demo: http://em.arseven.at

## Updates

These updates are mainly for me so I keep track of the additions to this project. Nonetheless, I publish them with this
readme in case anyone looking at this project needs a bit more narrative to my commits 😛.

> 9 August 2020 - Moving to Pandas
> With this commit all dictionary based data structure are moving to dataframes. This allowes me to also store the
> datetime of each price and enables easier calculations based on weekly/monthly/yearly returns. In addition a helper
> file has been added that contains most calculations like calculating the var-cov matrix or computing weights. So,
> in general this commit is an enhancement for the features that are working so far. Next up, more portfolios and
> fixing the DCF calculation.

> 18 July 2020 - Initial Commit
>
> Even though the initial commit lies almost two weeks in the past, this commit marks the true initial commit.
> The overall layout of the html pages is cleaned up and the core functionalities' basis has also been finished.
> In the upcoming updates the portfolio construction including plotting the efficient frontier should be finished.
> After the DCF analysis will be improved as it currently still computes extreme results for some companies.

> 8 July 2020 - Hello World.
>
> After tinkering around with my daytrading bot I chose to incorporate it into a more useful and bigger tool.
> Thus, I am launching the equity manager that should inherit the trading functions from the daytrading bot.
> However, this project adds financial analysis and trading decision based on fundamentals to the mix. In
> addition important theories like the modern portfolio theory will also be incorporated to construct the
> optimal portfolio.
