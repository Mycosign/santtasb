/*1678729588000*/
function replaceSiteWideVariables() {
    $(".san-branch-count").text(`${branchCount}`);
    $(".san-mob-app-users").text(`${mobileAppUsers}`);
    $(".san-mob-app-date").text(`${mobileAppUsersUpdateDate}`)
}
var userIP;
var didLoadThreatMetrix = false;
var UNIQUE_SESSION_ID = Date.now() + Math.random().toString().substr(2, 9);

function gotoTMX(ok, ko) {
    loadThreatMetrix();
    $.getJSON("https://api.ipify.org?format\x3djsonp\x26callback\x3d?", function(json) {
        userIP = json.ip;
        Liferay.Service("/santander.promocode/sf-l-rval-ddajson", {
            siteId: Liferay.ThemeDisplay.getScopeGroupId(),
            userIP: userIP,
            uniqueSessionID: UNIQUE_SESSION_ID
        }, function(obj) {
            if (obj == "pass") {
                var tmstp = Date.now() * Math.floor(Math.random() * 1E3) + 1;
                tmstp = tmstp.toString();
                tmstp = tmstp.slice(0, 9);
                var gid = getCookie("_gid");
                gid = gid.substring(6);
                var ga_cid = getCookie("ga_cid");
                window.location.assign(ok +
                    "\x26_ga\x3d2." + tmstp + "." + gid + "-" + ga_cid)
            } else window.location.assign(ko)
        })
    })
}

function getCookie(cname) {
    var name = cname + "\x3d";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(";");
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == " ") c = c.substring(1);
        if (c.indexOf(name) == 0) return c.substring(name.length, c.length)
    }
    return ""
}

function loadThreatMetrix() {
    if (didLoadThreatMetrix) return;
    $.getJSON("https://api.ipify.org?format\x3djsonp\x26callback\x3d?", function(json) {
        userIP = json.ip;
        didLoadThreatMetrix = true
    })
}
Liferay.on("allPortletsReady", function() {
    $(".nav-menu").on("shown.bs.collapse", function() {
        $(".nav-menu").addClass("active")
    });
    $(".nav-menu").on("hidden.bs.collapse", function() {
        $(".nav-menu").removeClass("active")
    });
    replaceSiteWideVariables()
});
$(document).ready(function() {
    if (pageIncludesTMX !== undefined && pageIncludesTMX) {
        let importedHead = document.createElement("script");
        importedHead.src = profilingEndpointUrl + "/fp/tags.js?org_id\x3d" + tmxOrganizationId + "\x26session_id\x3d" + UNIQUE_SESSION_ID;
        importedHead.dataset.senaTrack = "temporary";
        document.head.appendChild(importedHead)
    }
});