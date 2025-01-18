function sleep (time){return new Promise((resolve) => setTimeout(resolve, time))}
var server_color = $('#server_color')[0].value;

function colorCorrect(new_id){
    if(new_id === NaN || new_id === '' || new_id === null || new_id === undefined){
        return server_color
    }
    return new_id
}

//// FUNCTIONAL FUNC
async function qr_gen(userid){
    let dt = {
        'serverid':$('#serverid')[0].value,
        'entityid':userid,
        'action':'get',
        'entitytype':'user',
        'extra':'req_qr_data'
    }
    $.ajax({
        url: '/_api/uconn/entitymodel',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            console.log(response);
            var svgNode = QRCode({
                msg :  response.qrcode
                ,dim :   250
                ,pad :   6
                ,mtx :   7
                ,ecl :  "H"
                ,ecb :   0
                ,pal : [server_color, "#ffffff"]
                ,vrb :   1
            });
            svgNode.classList.add("rounded","mx-auto","d-block");
            $('#showQRLabel')[0].innerHTML = response.answer.name;
            $('#showQRCode')[0].innerHTML = '';
            $('#showQRCode')[0].append(svgNode);
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
        }
    });
}

async function face_auth(open, id){
    if(open){
        $('#registerFidUserId')[0].value=id;
        $('#registerFidResponse')[0].innerHTML = '';
        $('#registerFidImg1')[0].disabled = false;
        $('#registerFidImg2')[0].disabled = false;
        $('#registerFidSubmit')[0].disabled = false;
        $('#registerFidImg1').val('');
        $('#registerFidImg2').val('');
        return
    }
    $('#registerFidImg1')[0].disabled = true;
    $('#registerFidImg2')[0].disabled = true;
    $('#registerFidResponse')[0].innerHTML = 'processing images...';
    $('#registerFidSubmit')[0].disabled = true;

    let image_data = new FormData();
    image_data.append('destination',$('#serverid')[0].value);
    image_data.append('userid',$('#registerFidUserId')[0].value);
    image_data.append('image1', $('#registerFidImg1')[0].files[0]);
    image_data.append('image2', $('#registerFidImg2')[0].files[0]);
    sc = false

    $('#registerFidResponse')[0].innerHTML = 'uploading images, this could take half a minute';

    await $.ajax({
        url: "/_api/uconn/imageupload",
        type: "POST",
        data: image_data,
        processData: false,
        contentType: false,
        success: function(response) {
            console.log(response);
            if(response === null){
                $('#registerFidResponse')[0].innerHTML = 'comparing images took too long, try again later';
                return
            }else if (response.code === '409') {
                $('#registerFidResponse')[0].innerHTML = 'the uploaded images do not match, try again later';
                return
            }else if(response.code !== '200'){
                $('#registerFidResponse')[0].innerHTML = 'upload failed, try again later';
                return
            }
            sc = true
            $('#registerFidResponse')[0].innerHTML = 'success, processing changes';
        },
        error: function(xhr, status, error) {
            console.error("Error uploading image:", error);
            $('#registerFidResponse')[0].innerHTML = 'exception happened while uploading images, try again later';
            return
        }
    });
    if(sc){
        await sleep(2000).then(() => {
            $('#registerFid').modal('hide');
        });
    }
}




//// MAIN

async function main(){
    let us = {
        'serverid':$('#serverid')[0].value
    }
    await $.ajax({
        url: '/_api/uconn/servermodel',
        type: 'POST',
        data: JSON.stringify(us),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            $('#uCardHolderKeys')[0].innerHTML = '';
            response.answer.forEach(sdata => {
                console.log(sdata);
                let key_symb = 'vpn_key_alert'
                if(sdata.static_unq !== '' && sdata.static_unq !== null){
                    key_symb = 'vpn_key'
                }
                $('#uCardHolderKeys')[0].innerHTML += `
                    <div class="card server_card o_server_card" style="border-color:${colorCorrect(sdata.color)}" id="usercard_${sdata.local_userid}">
                        <div class="card-body" style="min-width: 20rem;">
                            <h5 class="card-title row gap-1">
                                <span class="col-10">${sdata.name}</span>
                                <span class="material-symbols-outlined col-1">
                                    ${key_symb}
                                </span>
                            </h5>
                            <p class="card-text">
                                <span class="col-7">last entry at ${sdata.last_logged}</span>
                            </p>
                            <a onclick="qr_gen('${sdata.local_userid}');" class="btn btn-primary col-3" style="background-color:${colorCorrect(sdata.color)};border-color:${colorCorrect(sdata.color)}" data-bs-toggle="modal" data-bs-target="#showQR">auth</a>
                            <a onclick="face_auth(true,'${sdata.local_userid}');" data-bs-toggle="modal" data-bs-target="#registerFid" class="btn btn-secondary col-4">faceauth</a>
                        </div>
                    </div>
                `;
            });
            if(response.answer.length === 0){
                $('#uCardHolderKeys')[0].innerHTML = '<p class="work-sans-lite mb-0">currently you dont have any keys assigned - but if you recieve some will be here</p>'
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            $('#cardHolderUsers')[0].innerHTML = '';
            $('#cardHolderUsers')[0].innerHTML = 'Error happened whilest getting this information. Please try again later.';
        }
    });
}

$(document).ready(function() {
    sleep(1000).then(() => {main('');});
});
