# Sourced by up.sh and down.sh after their api(): the account's pods this
# project made, one "<id> <status>" line each (0043 design D2).

# isekai_pods: every page, since v2 filters nothing; a failed page returns non-zero.
# A TERMINATED pod bills nothing and cannot be deleted again, so it is not listed.
isekai_pods() {
  local image page more cursor=""
  image=$(jq -r '.image' config/image.json) || return 1
  while :; do
    page=$(api -f "$API/pods?limit=1000${cursor:+&cursor=$(jq -rn --arg c "$cursor" '$c|@uri')}") \
      || return 1
    echo "$page" | jq -r --arg image "$image" \
      '.pods[] | select(.name == "isekai" and ((.image // "") | startswith($image))
                        and .status != "TERMINATED")
       | "\(.id) \(.status)"' 2>/dev/null \
      || return 1
    more=$(echo "$page" | jq -r '.pagination.hasNextPage') || return 1
    [ "$more" = "true" ] || return 0
    cursor=$(echo "$page" | jq -er '.pagination.nextCursor') || return 1
  done
}
