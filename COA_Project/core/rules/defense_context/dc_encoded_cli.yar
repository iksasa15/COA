/*
  Defense-context: common attacker-style command-line markers (generic).
  Not a vendor attribution rule — tune for your environment.
*/
rule dc_encoded_cli {
  meta:
    description = "Suspicious encoded/split command invocation patterns"
    severity = "MEDIUM"
  strings:
    $a = "-enc" nocase
    $b = "-e " nocase wide ascii
    $c = "-encodedcommand" nocase
  condition:
    uint16(0) == 0x5a4d and any of them
}
