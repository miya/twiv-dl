// 検索ボタンを押した時の処理
const submitBtn = document.getElementById("searchBtn");
submitBtn.onclick = () => {
    const inputUrl = document.getElementById("inputForm");
    if (inputUrl.value==="") {
        alert(false, "URLを入力してください。");
    } else {
        postData(inputUrl.value);
    }
    inputUrl.value = "";
};


// アラートを表示させる
const alert = (status, message) => {
    const alertEle = document.getElementById("alert");
    let alert_icon
    let alert_color
    if (status) {
        alert_icon = "<strong><i class=\"fas fa-check\"></i></strong>";
        alert_color = "success"
    } else {
        alert_icon =  "<strong><i class=\"fas fa-exclamation-circle\"></i></strong>";
        alert_color = "danger"
    }
    const alertHtml = `<div class="alert alert-${alert_color}" role="alert">${alert_icon} ${message}</div>`;
    alertEle.style.display = "block";
    alertEle.innerHTML = alertHtml;
};


// 動画を表示させる
const video = (videoData) => {
    let videoUrl = ""
    const videoEle = document.getElementById("video");
    if ("large" in videoData) {
        videoUrl = videoData["large"]["url"]
    } else if ("medium" in videoData) {
        videoUrl = videoData["medium"]["url"]
    } else if ("small" in videoData) {
        videoUrl = videoData["small"]["url"]
    }
    const videoHtml = `<div class="embed-responsive embed-responsive-16by9"><iframe class="embed-responsive-item" src="${videoUrl}" allowfullscreen></iframe></div>`;
    videoEle.style.display = "block";
    videoEle.innerHTML = videoHtml;
};


// ダウンロードボタンを表示させる
const dlBtns = (videoData) => {
    let inputHtml = "<p class=\"text-muted\">ダウンロード</p>";
    if ("small" in videoData) {
        inputHtml += `<a href="download/small" class="pr-2">${videoData["small"]["size"]}</a>`
    }
    if ("medium" in videoData) {
        inputHtml += `<a href="download/medium" class="pr-2">${videoData["medium"]["size"]}</a>`
    }
    if ("large" in videoData) {
        inputHtml += `<a href="download/large" class="pr-2">${videoData["large"]["size"]}</a>`
    }
    const dlBtnsEle = document.getElementById("dlBtns");
    dlBtnsEle.style.display = "block";
    dlBtnsEle.innerHTML = inputHtml;
};


// サーバーと通信する際の処理
const postData = (url) => {
    return fetch("/search", {
        method: "POST",
        body : JSON.stringify({inputUrl: url}),
        headers: {"Content-Type": "application/json"}
    })
        .then(response => response.json())
        .then(data => {
            const status = data["status"];
            const message = data["message"];
            const description = data["description"];
            alert(status, message, description);
            if (status) {
                const videoData = data["data"];
                video(videoData);
                dlBtns(videoData);
            }
        })
        .catch(error => {
            console.log("error: ", error);
            alert(false, "サーバーとの通信に失敗しました");
        });
};