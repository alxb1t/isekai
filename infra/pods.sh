# Sourced by up.sh and down.sh after their api(): the account's pods this
# project made, one "<id> <status>" line each (0043 design D2).

# isekai_pods: every page, since v2 filters nothing; a failed page returns non-zero.
# A TERMINATED pod bills nothing and cannot be deleted again, so it is not listed.
# A fault fails the listing rather than hanging or missing a pod (0044 design D1).
isekai_pods() {
  local image page bare more next cursor=""
  image=$(jq -r '.image' config/image.json) || return 1
  while :; do
    page=$(api -f "$API/pods?limit=1000${cursor:+&cursor=$(jq -rn --arg c "$cursor" '$c|@uri')}") \
      || return 1
    # A pod named 'isekai' with no image cannot be told to be this project's or not.
    bare=$(echo "$page" | jq -r \
      '.pods[] | select(.name == "isekai" and (.image // "") == "") | .id' 2>/dev/null) \
      || return 1
    if [ -n "$bare" ]; then
      echo "pod $(echo "$bare" | paste -sd, -) is named 'isekai' but carries no image" >&2
      return 1
    fi
    # A look-alike image, one whose name only begins with this project's, is not ours.
    echo "$page" | jq -r --arg image "$image" \
      '.pods[] | select(.name == "isekai" and .status != "TERMINATED"
                        and (.image == $image or (.image | startswith($image + "@"))
                             or (.image | startswith($image + ":"))))
       | "\(.id) \(.status)"' 2>/dev/null \
      || return 1
    more=$(echo "$page" | jq -r '.pagination.hasNextPage') || return 1
    [ "$more" = "true" ] || return 0
    next=$(echo "$page" | jq -er '.pagination.nextCursor') || return 1
    if [ "$next" = "$cursor" ]; then
      echo "the pod listing answered cursor $next twice" >&2
      return 1
    fi
    cursor=$next
  done
}
