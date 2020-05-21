# PROJECT WATER QUALITY INDEX

### Background  

Water quality monitoring is one of the most important pillars in water resource management.
However, water quality monitoring can be resource intensive, especially for developing countries with limited resources.
As such, Water Quality Indexes (WQI) are developed as a convenient tool to summarise general water quality
---  


The following web application allows user to input measured water quality parameters, which subsequently will generate a WQI.
Users can also input an ID, date, and location for each observation, which will be saved into a sqlite database.
Users can also choose to upload their data in a csv format, if they already have their own data.
The observations will be displayed in interactive charts (using [Chart.js](https://github.com/chartjs/Chart.js))) and map (using [Leaflet](https://leafletjs.com)).
The interactive charts allow users to look at spatial and temporal trends of the water quality.
The user can also download the data in a csv format for further processing.
---

The output includes:
* WQI<sub>NON-WEIGHTED</sub> (Water quality parameters have equal weights
* WQI<sub>WEIGHTED</sub> (Water quality parameters have different weights
* WQI<sub>ADJUSTED</sub> (Adjusted for missing values)
* WQI<sub>NON-ADJUSTED</sub> (Not adjusted for missing value. By default, gives an **__NA__**)  

Checkout the [video demo here](https://youtu.be/wn9VnwnF5pI)
