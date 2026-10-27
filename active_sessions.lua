local cursor = "0"
local sessions = {}

repeat
    local result = redis.call("SCAN", cursor, "MATCH", "recovery:session:*", "COUNT", 100)
    cursor = result[1]

    for _, key in ipairs(result[2]) do
        local user_id = redis.call("GET", key)

        if user_id then
            table.insert(sessions, "user_id=" .. user_id)
        end
    end
until cursor == "0"

return sessions
