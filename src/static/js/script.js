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
    let alertIcon;
    let alertColor;
    if (status) {
        alertIcon = "<strong><i class=\"fas fa-check\"></i></strong>";
        alertColor = "success"
    } else {
        alertIcon =  "<strong><i class=\"fas fa-exclamation-circle\"></i></strong>";
        alertColor = "danger";
    }
    const alertHtml = `<div class="alert alert-${alertColor}" role="alert">${alertIcon} ${message}</div>`;
    alertEle.style.display = "block";
    alertEle.innerHTML = alertHtml;
};


// 動画を表示させる
const video = (displayVideoUrl) => {
    const videoEle = document.getElementById("video");
    const videoHtml = `<div class="embed-responsive embed-responsive-16by9"><iframe class="embed-responsive-item" src="${displayVideoUrl}" allowfullscreen></iframe></div>`;
    videoEle.style.display = "block";
    videoEle.innerHTML = videoHtml;
};


// ダウンロードボタンを表示させる
const dlBtns = (sizes) => {
    let inputHtml = '<p class="text-muted">ダウンロード</p>';
    const sizeLabel = ["small", "medium", "large"];
    for (let i = 0; i<sizes.length; i++) {
         inputHtml += `<a href="download/${sizeLabel[i]}" class="pr-2">${sizes[i]}</a>`
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
        .then(videoData => {
            const status = videoData["status"];
            const message = videoData["message"];
            alert(status, message);
            if (status) {
                const displayVideoUrl = videoData["display_video_url"];
                const sizes = videoData["sizes"];
                video(displayVideoUrl);
                dlBtns(sizes);
            }
        })
        .catch(error => {
            console.log("error: ", error);
            alert(false, "サーバーとの通信に失敗しました");
        });
};