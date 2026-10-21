# Code Citations

## License: unknown
https://github.com/diclophis/sig/blob/b0655c73da4dcf2b04f9600860b51a66097cf0ab/include/Calendar/docs/examples/20.php

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody
```


## License: unknown
https://github.com/dysbulic/tip/blob/9c48c396a796a193ddd7489cb86c4c76c09d36fe/site/3and.net/brett%27s_schedule.html

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody
```


## License: unknown
https://github.com/kirkeby/django-stuff/blob/7f9d35391aa9cd2359eb7fbad70c9139506176bc/src/ibofobi/apps/calendar/templates/calendar/month.html

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:
```


## License: unknown
https://github.com/diclophis/sig/blob/b0655c73da4dcf2b04f9600860b51a66097cf0ab/include/Calendar/docs/examples/20.php

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody
```


## License: unknown
https://github.com/dysbulic/tip/blob/9c48c396a796a193ddd7489cb86c4c76c09d36fe/site/3and.net/brett%27s_schedule.html

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody
```


## License: unknown
https://github.com/kirkeby/django-stuff/blob/7f9d35391aa9cd2359eb7fbad70c9139506176bc/src/ibofobi/apps/calendar/templates/calendar/month.html

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:
```


## License: unknown
https://github.com/katiesul/VisitDayScheduler/blob/528ffe883a701df85d1412464388f0ed465a4489/VisitDayScheduler/src/tests/Tests.java

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          
```


## License: unknown
https://github.com/devenkapadia/EV-ChargeSlotBooking/blob/b981dc5f6654db11b8624661414fcab7bb9e8c7f/Half_charge.html

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          
```


## License: unknown
https://github.com/katiesul/VisitDayScheduler/blob/528ffe883a701df85d1412464388f0ed465a4489/VisitDayScheduler/src/tests/Tests.java

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          
```


## License: unknown
https://github.com/devenkapadia/EV-ChargeSlotBooking/blob/b981dc5f6654db11b8624661414fcab7bb9e8c7f/Half_charge.html

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          
```


## License: unknown
https://github.com/katiesul/VisitDayScheduler/blob/528ffe883a701df85d1412464388f0ed465a4489/VisitDayScheduler/src/tests/Tests.java

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          
```


## License: unknown
https://github.com/devenkapadia/EV-ChargeSlotBooking/blob/b981dc5f6654db11b8624661414fcab7bb9e8c7f/Half_charge.html

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          
```


## License: unknown
https://github.com/katiesul/VisitDayScheduler/blob/528ffe883a701df85d1412464388f0ed465a4489/VisitDayScheduler/src/tests/Tests.java

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          "11:30AM-12:00PM", "12:00PM-12:30PM", "12:30PM-1:00PM", "1:00PM-1:30PM", 
          "1:30PM-2:00PM", "2:00PM-
```


## License: unknown
https://github.com/devenkapadia/EV-ChargeSlotBooking/blob/b981dc5f6654db11b8624661414fcab7bb9e8c7f/Half_charge.html

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          "11:30AM-12:00PM", "12:00PM-12:30PM", "12:30PM-1:00PM", "1:00PM-1:30PM", 
          "1:30PM-2:00PM", "2:00PM-
```


## License: unknown
https://github.com/katiesul/VisitDayScheduler/blob/528ffe883a701df85d1412464388f0ed465a4489/VisitDayScheduler/src/tests/Tests.java

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          "11:30AM-12:00PM", "12:00PM-12:30PM", "12:30PM-1:00PM", "1:00PM-1:30PM", 
          "1:30PM-2:00PM", "2:00PM-2:30PM", "2:30PM-3:00PM", "3:00PM-3:30PM", 
          "3:30PM-4:00PM", "4:00PM-4:30PM", "4:30PM-5:00PM", "
```


## License: unknown
https://github.com/devenkapadia/EV-ChargeSlotBooking/blob/b981dc5f6654db11b8624661414fcab7bb9e8c7f/Half_charge.html

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          "11:30AM-12:00PM", "12:00PM-12:30PM", "12:30PM-1:00PM", "1:00PM-1:30PM", 
          "1:30PM-2:00PM", "2:00PM-2:30PM", "2:30PM-3:00PM", "3:00PM-3:30PM", 
          "3:30PM-4:00PM", "4:00PM-4:30PM", "4:30PM-5:00PM", "
```


## License: unknown
https://github.com/katiesul/VisitDayScheduler/blob/528ffe883a701df85d1412464388f0ed465a4489/VisitDayScheduler/src/tests/Tests.java

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          "11:30AM-12:00PM", "12:00PM-12:30PM", "12:30PM-1:00PM", "1:00PM-1:30PM", 
          "1:30PM-2:00PM", "2:00PM-2:30PM", "2:30PM-3:00PM", "3:00PM-3:30PM", 
          "3:30PM-4:00PM", "4:00PM-4:30PM", "4:30PM-5:00PM", "
```


## License: unknown
https://github.com/devenkapadia/EV-ChargeSlotBooking/blob/b981dc5f6654db11b8624661414fcab7bb9e8c7f/Half_charge.html

```
Here's the complete updated code for your schedule page:

```html
{% extends "base.html" %}
{% block content %}

<style>
  :root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    
    /* Lab Color Indicators */
    --clr-all: #64748b;
    --clr-cs: #10b981;
    --clr-db: #3b82f6;
    --clr-embedded: #ec4899;
    --clr-iot: #f59e0b;
    --clr-multimedia: #a855f7;
    --clr-network: #ef4444;
  }

  .schedule-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    font-family: inherit;
    margin-top: 20px;
  }

  /* Header Section */
  .schedule-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }
  .schedule-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  .schedule-title span {
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Filter Pills */
  .filter-section {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .filter-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }
  .filter-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: #fff;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .filter-pill:hover {
    background: #f1f5f9;
  }
  .filter-pill.active {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }

  /* Timetable Grid */
  .table-responsive {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  .schedule-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    background: #fff;
  }
  .schedule-table th, 
  .schedule-table td {
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    font-size: 12px;
    height: 20px;
  }
  .schedule-table th {
    background-color: #f8fafc;
    color: var(--text-primary);
    font-weight: 600;
  }
  .time-col {
    background-color: #f8fafc;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    width: 130px;
    text-align: center;
  }

  .schedule-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

<div class="page-header">
  <div>
    <h1>Schedule</h1>
    <p>CCS Laboratory Weekly Schedule Management.</p>
  </div>
</div>

<div class="schedule-container">
  <div class="schedule-header">
    <h2 class="schedule-title">
      Laboratory <span>· Weekly Schedule</span> | CCS LAMS | <span>Sem/SY:</span> 2 / 2025-2026
    </h2>
  </div>

  <div class="filter-section">
    <span class="filter-label">Filter:</span>
    <button class="filter-pill active" data-lab="all"><span class="dot" style="background-color: var(--clr-all)"></span>All labs</button>
    <button class="filter-pill" data-lab="CS Lab"><span class="dot" style="background-color: var(--clr-cs)"></span>CS Lab</button>
    <button class="filter-pill" data-lab="Database Lab"><span class="dot" style="background-color: var(--clr-db)"></span>Database Lab</button>
    <button class="filter-pill" data-lab="Embedded Lab"><span class="dot" style="background-color: var(--clr-embedded)"></span>Embedded Lab</button>
    <button class="filter-pill" data-lab="IOT Lab"><span class="dot" style="background-color: var(--clr-iot)"></span>IOT Lab</button>
    <button class="filter-pill" data-lab="Multimedia Lab"><span class="dot" style="background-color: var(--clr-multimedia)"></span>Multimedia Lab</button>
    <button class="filter-pill" data-lab="Network Lab"><span class="dot" style="background-color: var(--clr-network)"></span>Network Lab</button>
  </div>

  <div class="table-responsive">
    <table class="schedule-table">
      <thead>
        <tr>
          <th style="text-align: center;">Time</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
          <th>Sunday</th>
        </tr>
      </thead>
      <tbody id="schedule-tbody">
        {% for time in [
          "7:30AM-8:00AM", "8:00AM-8:30AM", "8:30AM-9:00AM", "9:00AM-9:30AM", 
          "9:30AM-10:00AM", "10:00AM-10:30AM", "10:30AM-11:00AM", "11:00AM-11:30AM", 
          "11:30AM-12:00PM", "12:00PM-12:30PM", "12:30PM-1:00PM", "1:00PM-1:30PM", 
          "1:30PM-2:00PM", "2:00PM-2:30PM", "2:30PM-3:00PM", "3:00PM-3:30PM", 
          "3:30PM-4:00PM", "4:00PM-4:30PM", "4:30PM-5:00PM", "
```

