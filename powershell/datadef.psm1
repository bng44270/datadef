class DataDefSchema {
    [System.Collections.Hashtable] $Schema = [System.Collections.Hashtable]::new()
    [System.Collections.Hashtable] $Types = @{
        "Double"  = "number"
        "Int32"   = "number"
        "Int64"   = "number"
        "String"  = "string"
        "Boolean" = "boolean"
    }

    [bool] ValidateType([string] $t) {
        return ($t -in $this.Types.Values)        
    }

    [bool] ValidateField([string] $f, [string] $v) {
        if (-not ($f -in $this.Schema.Keys)) {
            throw "Field not found in schema ($f)"
        }

        $dataType = $v.GetType().Name

        if (-not ($dataType -in $this.Types.Keys)) {
            throw "Data type not supported ($dataType)"
        }

        return ($this.Schema[$f] -eq $this.Types[$dataType])
    }
    
    [void] AddField([string] $f, [string] $t) {
        if (-not $this.ValidateType($t)) {
            throw "Invalid field type ($t)"
        }

        if ($f -in $this.Schema.Keys) {
            throw "Field already exists in schema ($f)"
        }

        $this.Schema[$f] = $t
    }

    [string] ToJson() {
        return ($this.Schema | ConvertTo-Json)
    }

    static [DataDefSchema] FromPSObj([pscustomobject] $j) {
        $ob = [DataDefSchema]::new()
        
        $j | Get-Member -MemberType NoteProperty | ForEach-Object {
            $field = $_.Name
            $type = $j."$field"

            $ob.AddField($field,$type)
        }

        return $ob
    }
}

class DataDefRow : System.Collections.Hashtable {
    DataDefRow() : base() { }
}

class DataDef {
    [DataDefSchema] $Schema
    [System.Collections.Generic.List[DataDefRow]] $Data

    DataDef() {
        $this.Schema = [DataDefSchema]::new()
        $this.Data = [System.Collections.Generic.List[DataDefRow]]::new()
    }

    DataDef([DataDefSchema]$s) {
        $this.Schema = $s
        $this.Data = [System.Collections.Generic.List[DataDefRow]]::new()
    }

    DataDef([DataDefSchema]$s,[System.Collections.Generic.List[DataDefRow]]$d) {
        $this.Schema = $s
        $this.Data = $d
    }

    [void] ValidateRow([DataDefRow]$r) {
        $r.Keys | ForEach-Object {
            $field = $_
            $value = $r."$field"
            
            $this.Schema.ValidateField($field,$value)
        }
    }

    [void] Insert([DataDefRow]$r) {
        $this.ValidateRow($r)

        $this.Data.Add($r)
    }

    [DataDef] Equal([string] $f, [string] $v) {
        $this.Schema.ValidateField($f,$v)

        $qdata = $this.Data | Where-Object { $_."$f" -eq $v}
        
        return ([DataDef]::new($this.Schema,$qdata))
    }

    [DataDef] Match([string] $f, [string] $v) {
        $this.Schema.ValidateField($f,$v)

        $qdata = $this.Data | Where-Object { $_."$f" -match $v}
        
        return ([DataDef]::new($this.Schema,$qdata))
    }

    [DataDef] GreaterThan([string] $f, [string] $v) {
        $this.Schema.ValidateField($f,$v)

        $qdata = $this.Data | Where-Object { $_."$f" -gt $v}
        
        return ([DataDef]::new($this.Schema,$qdata))
    }

    [DataDef] GreaterThanOrEqual([string] $f, [string] $v) {
        $this.Schema.ValidateField($f,$v)

        $qdata = $this.Data | Where-Object { $_."$f" -ge $v}
        
        return ([DataDef]::new($this.Schema,$qdata))
    }

    [DataDef] LessThan($f,$v) {
        $this.Schema.ValidateField([string] $f, [string] $v)

        $qdata = $this.Data | Where-Object { $_."$f" -lt $v}
        
        return ([DataDef]::new($this.Schema,$qdata))
    }

    [DataDef] LessThanOrEqual([string] $f, [string] $v) {
        $this.Schema.ValidateField($f,$v)

        $qdata = $this.Data | Where-Object { $_."$f" -le $v}
        
        return ([DataDef]::new($this.Schema,$qdata))
    }

    [string] ToJson() {
        return ($this.Data | ConvertTo-Json)
    }

    static [DataDef] FromPSObj([DataDefSchema]$s,[Object[]] $j) {
        $ob = [DataDef]::new($s)

        $j | ForEach-Object {
            $row = $_
            $rowHash = [DataDefRow]::new()

            $s.Schema.Keys | ForEach-Object {
                $field = $_
                $value = $row."$field"

                $rowHash[$field] = $value
            }
            
            $ob.Insert($rowHash)
        }

        return $ob
    }
}
