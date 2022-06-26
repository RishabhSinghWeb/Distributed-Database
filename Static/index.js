var username, MaxAge, Path, form;
display = document.getElementById("display")

function check_auth() {
    document.cookie.split(";").forEach((cookie) => {
        cookie = cookie.trim().split("=")
        if (cookie[0] == "username")
            username = cookie[1]
    })
    if (username) {
        display_home()
        refresh_messages()
    } else
        display_login()
}

function send_req(type, location, data) {
    var Req = new XMLHttpRequest();
    Req.onreadystatechange = function() {
        if (Req.readyState === 4) {
            check_auth()
            if (Req.status){
                if (Req.status != 200)
                    display.append("Something bad happened:", Req.statusText)
            }
            else
                display.append("Something bad happened: Server didn't reply")
        }
    }
    Req.open(type, location);
    Req.send(data);
}

function login() {
    form = display.children[0]
    send_req("POST", "/api/login", JSON.stringify({
        username: form["username"].value,
        password: form["password"].value
    }));
}

function logout() {
    document.cookie = "username="
    username = null
    display_login()
    send_req("DELETE", "/api/login")
}

function send_message() {
    send_req("POST", "/api/messages", document.getElementById("message_input").value)
}

function delete_message(uuid) {
    send_req("DELETE", "/api/messages", uuid)
}

function refresh_messages() {
    var Req = new XMLHttpRequest();
    Req.open("GET", "/api/messages");
    Req.onload = function() {
        html = "<table>"
        JSON.parse(JSON.parse(Req.response).value).value.forEach((message) => {
            html += "<tr><td>" + message.value + "</td><td>" + message.username + "</td><td>"
            if (username == message.username)
                html += `<button onclick="delete_message('` + message.key + `')">Delete</button>`
            html += "</td></tr>"
        })
        document.getElementById("messages").innerHTML = html + "</table>"
    }
    Req.send();
}

function display_login() {
    display.innerHTML = `<form>
                            <table>
                                <tr>
                                    <td>
                                        <lable>Name</lable>
                                    </td>
                                    <td>
                                        <input name="username" value="Guest"></input>
                                    <td>
                                </tr>
                                <tr>
                                    <td>
                                        <lable>Password</lable>
                                    </td>
                                    <td>
                                        <input name="password" type="password">
                                    </td>
                                </tr>
                            </table>
                            <button type="button" onclick="login()">Log in!</button>
                        </form>`
}

function display_home() {
    display.innerHTML = `<H1>messages</H1>
                        <form>
                            <label>
                                New message
                                <input id="message_input" type="text" name="note">
                                <input style="display:none;">
                                <button type="button" onclick="send_message()">Send it!</button>
                            </label>
                        </form>
                        <button onclick="logout()">Logout</button>
                        <br>
                        <div id="messages">
                        </div>`
}
check_auth()