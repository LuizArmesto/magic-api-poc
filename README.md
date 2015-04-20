# Magic API - Proof of Concept

## Usage

### Initializing Database

```
python manage.py -d 'http://data.okfn.org/data/cpi/' initdb
```

### Populating Database

```
python manage.py -d 'http://data.okfn.org/data/cpi/' importdata
```

### Starting API server

```
python manage.py -d 'http://data.okfn.org/data/cpi/' run
```

### Example

`http://127.0.0.1:5000/api/cpi/cpi?year=2008-01-01&year=2010-01-01&countryCode=BRA&countryCode=USA&countryCode=FRA`

Result:
```
[
    {
        "_uid": 793,
        "countryCode": "BRA",
        "countryName": "Brazil",
        "cpi": 119.662260364,
        "year": "2009-01-01"
    },
    {
        "_uid": 794,
        "countryCode": "BRA",
        "countryName": "Brazil",
        "cpi": 125.6912243062,
        "year": "2010-01-01"
    },
    {
        "_uid": 2113,
        "countryCode": "FRA",
        "countryName": "France",
        "cpi": 106.194184839,
        "year": "2009-01-01"
    },
    {
        "_uid": 2114,
        "countryCode": "FRA",
        "countryName": "France",
        "cpi": 107.818572912,
        "year": "2010-01-01"
    },
    {
        "_uid": 6525,
        "countryCode": "USA",
        "countryName": "United States",
        "cpi": 109.8546618306,
        "year": "2009-01-01"
    },
    {
        "_uid": 6526,
        "countryCode": "USA",
        "countryName": "United States",
        "cpi": 111.6563260081,
        "year": "2010-01-01"
    }
]```
