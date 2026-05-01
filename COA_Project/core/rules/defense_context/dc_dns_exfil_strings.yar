rule dc_dns_exfil_strings {
  meta:
    description = "DNS / tunneling related strings (coarse heuristic)"
    severity = "LOW"
  strings:
    $t = "TXT record" nocase
  condition:
    uint16(0) == 0x5a4d and filesize < 8MB and $t
}
