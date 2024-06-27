# RPA - Reuters News
The project works but needs a proxy or vpn when execute into Cloud Room because the IP maybe have a lot of works but with a appropriate IP works great!

When fails save the source code page ('source_code.html') to analyze and prevent futures issues.

## Input

### Schema
```
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "phrase": {
      "type": "string",
      "description": "Phrase to search"
    },
    "section": {
      "type": "string",
      "description": "Section of the news"
    },
    "months_ago": {
      "type": "integer",
      "description": "Number of months to consult",
      "minimum": 0
    }
  },
  "required": ["phrase", "months_ago"],
  "additionalProperties": false
}
```

### Example
```
{
    "phrase": "Joe Biden",
    "section": "Markets",
    "months_ago": 1
}
```

### Output
1. ./output/{phrase}.xlsx
2. ./output/img with all pictures

## Author
**Orlando Hernández Hernández**

## License
Orlando Hernández Hernández