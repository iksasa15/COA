rule dc_lolbins {
  meta:
    description = "LOLBins sometimes abused in regional campaigns (generic strings)"
    severity = "LOW"
  strings:
    $r = "rundll32" nocase
    $m = "mshta" nocase
    $w = "regsvr32" nocase
  condition:
    uint16(0) == 0x5a4d and 2 of them
}
