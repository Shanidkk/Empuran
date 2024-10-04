"""Picks error messages out of drive logs for surfacing to users."""

import json
import re
import sys

if len(sys.argv) != 1:
  print(f'Usage: {sys.argv[0]} (send drive logs on stdin)')
  sys.exit(1)

# LINT.IfChange(drivetimeout)
timeout_pattern = 'QueryManager timed out'
# LINT.ThenChange()

log_prefix_re = re.compile(
    r'^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z[IWEF]) '
)

suppressed_errors = (
    # Internal errors, should be silently retried inside DriveFS.
    'internalError Internal Error',
    'conflict File ID already exists',
    'deadlineExceeded A deadline was exceeded',
    'transientError Transient failure',

    # User-triggerable & surfaced as specific errors (EACCESS, ENOENT, etc).
    'conditionNotMet Precondition Failed',
    'authError Invalid Credentials',
    'forbidden File not mutable',
    'forbidden Insufficient permissions for this file',
    'notFound File not found',
)

acc = ''
last_stamp = ''
for line in sys.stdin:
  if not acc:
    if timeout_pattern in line:
      print(line, end='', flush=True)
      continue
    maybe_stamp = log_prefix_re.match(line)
    if maybe_stamp:
      last_stamp = maybe_stamp.group(1)
  # pylint: disable=line-too-long
  # An example logged value is:
  # 2021-03-23T15:58:56.231ZE [201:core_117860867942433405545] drive_v2_cloud_store.cc:424242:FAKE FAKE FAKE
  # {
  #  "error": {
  #   "errors": [
  #    {
  #     "domain": "usageLimits",
  #     "reason": "quotaExceeded",
  #     "message": "The download quota for this file has been exceeded",
  #     "locationType": "other",
  #     "location": "quota.download"
  #    }
  #   ],
  #   "code": 403,
  #   "message": "The download quota for this file has been exceeded"
  #  }
  # }
  # Or
  # 2021-03-23T15:58:56.231ZE [201:core_117860867942433405545] drive_v2_cloud_store_no_apiary.cc:3593:DumpToLog Response body 0x56f3ff6554b8: {
  #  "error": {
  #   "errors": [
  #    {
  #     "domain": "usageLimits",
  #     "reason": "quotaExceeded",
  #     "message": "The download quota for this file has been exceeded",
  #     "locationType": "other",
  #     "loca...
  # (with truncation)
  # pylint: enable=line-too-long

  def emit(r, m):
    if r and m:
      msg = f'{r} {m}'
      if not any(x in msg for x in suppressed_errors):
        print(f'{last_stamp} {msg}', flush=True)

  if line.rstrip() == '{' or ('DumpToLog Response body' in line and
                              line.rstrip().endswith('{')):
    acc = '{'
  elif acc:
    acc += line
  if acc and line.rstrip().endswith('...'):  # b/183502229
    reason, message = '', ''
    for l in acc.split('\n'):
      if '"reason":' in l:
        reason = l.split(':', 2)[1].strip(' \t\n\r,"')
      if '"message":' in l:
        message = l.split(':', 2)[1].strip(' \t\n\r,"')
    emit(reason, message)
    acc = ''
  if acc and line.rstrip() == '}':
    try:
      parsed = json.loads(acc)
    except json.JSONDecodeError:
      acc = ''
      continue
    try:
      e = parsed['error']['errors'][0]
    except:  # pylint: disable=bare-except
      acc = ''
      continue
    emit(e['reason'], e['message'])
    acc = ''
