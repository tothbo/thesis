function sleep (time){return new Promise((resolve) => setTimeout(resolve, time))}
var server_color = $('#server_color')[0].value;
function colorCorrect(new_id){
    if(new_id === NaN || new_id === '' || new_id === null || new_id === undefined){
        return server_color
    }
    return new_id
}

async function new_cam(backways){
    if(backways === undefined || backways === false){
        $('#cardNewCam')[0].classList.add('d-none');
        $('#cardHolderCam')[0].innerHTML = `
            <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${colorCorrect()}" id="camcard_new">
                <div class="card-body" style="min-width: 20rem;">
                    <h5 class="card-title row gap-1">
                        <span class="col-6 fst-italic">new</span>
                        <a onclick="cam_add('${colorCorrect()}');" class="btn btn-primary material-symbols-outlined col-2 card-sett" style="background-color:${colorCorrect()};border-color:${colorCorrect()};font-size:0.5rem;">save</a>
                        <a onclick="new_cam(true);" class="btn btn-secondary material-symbols-outlined mr-1 col-2 card-sett" style="font-size:0.5rem;">cancel</a>
                        <span class="material-symbols-outlined col-1">
                            nest_cam_outdoor
                        </span>
                    </h5>
                    <p class="card-text">
                        <form class="col-12">
                            <div class="mb-2">
                                <label for="camSettingsInputStream" class="form-label">rtsp stream</label>
                                <input type="text" class="form-control" id="camSettingsInputStream" value="" />
                            </div>
                        </form>
                    </p>
                </div>
            </div>
        ` + $('#cardHolderCam')[0].innerHTML;
        return
    }
    $('#cardNewCam')[0].classList.remove('d-none');
    $('#camcard_new').remove();
}

async function cam_rem(card_id, camid, server_color){
    let a = $('#'+card_id)[0];
    var dt = {
        'serverid':$('#serverid')[0].value,
        'entitytype':'camera',
        'entityid':camid,
        'action':'remove',
        'extra':''
    }
    process_data = true;

    $(a).find('.card-text')[0].innerHTML = "<div class='spinner-grow text-primary' style='background-color:"+server_color+"' role='status'><span class='visually-hidden'>Loading...</span></div>";

    // get new data / submit modifications
    await sleep(1000);
    await $.ajax({
        url: '/_api/sconn/entitymodel',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            console.log(response);
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            $(a).find('.card-text')[0].innerHTML = 'Cant load settings - exception happened in the request';
            process_data = false
        }
    });
    if(process_data){$('#cardHolderCam')[0].innerHTML = `<div class="spinner-grow text-primary" role="status"><span class="visually-hidden">Loading...</span></div>`;main('camera');}
}

async function cam_add(server_color){
    let a = $('#camcard_new')[0];
    var dt = {
        'serverid':$('#serverid')[0].value,
        'entitytype':'camera',
        'entityid':$(a).find('#camSettingsInputStream')[0].value,
        'action':'add',
        'extra':''
    }
    process_data = true;

    $(a).find('.card-text')[0].innerHTML = "<div class='spinner-grow text-primary' style='background-color:"+server_color+"' role='status'><span class='visually-hidden'>Loading...</span></div>";

    // get new data / submit modifications
    await sleep(1000);
    await $.ajax({
        url: '/_api/sconn/entitymodel',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            console.log(response);
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            $(a).find('.card-text')[0].innerHTML = 'Cant load settings - exception happened in the request';
            process_data = false
        }
    });
    if(process_data){$('#cardHolderCam')[0].innerHTML = `<div class="spinner-grow text-primary" role="status"><span class="visually-hidden">Loading...</span></div>`;main('camera');}
}

//// MAIN

async function main(hotreload_part){
    if(hotreload_part === 'camera' || hotreload_part === ''){
        // USERS
        let us = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'camera'
        }
        await $.ajax({
            url: '/_api/sconn/servermodel',
            type: 'POST',
            data: JSON.stringify(us),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                $('#cardHolderCam')[0].innerHTML = '';
                response.answer.forEach(sdata => {
                    console.log(sdata);
                    $('#cardHolderCam')[0].innerHTML += `
                        <div class="card o_cam_card" aria-hidden="true" style="border-color:${colorCorrect(sdata.color)}" id="camcard_${sdata.local_correlid}">
                            <div class="card-body">
                                <h5 class="card-title row gap-1">
                                <span class="col-10">${sdata.rtsp_host.split('/')[2]}</span>
                                <a href="javascript:cam_rem('camcard_${sdata.local_correlid}','${sdata.local_correlid}','${colorCorrect(sdata.color)}');" class="material-symbols-outlined remove-icon col-1" style="text-decoration: none;color:${colorCorrect(sdata.color)}!important;">
                                    nest_cam_outdoor
                                </a>
                                </h5>
                                <div class="card-text">
                                    <p class="work-sans-lite">connecting to rtsp stream...</p>
                                </div>
                            </div>
                        </div>
                    `;
                });
                $('#cardNewCam')[0].classList.remove('d-none');
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseText);
                $('#cardHolderCam')[0].innerHTML = '';
                $('#cardHolderCam')[0].innerHTML = 'Error happened whilest getting this information. Please try again later.';
            }
        });
        $('#cardHolderCam').on('mouseover', '.remove-icon', function() {
            let symbl = $(this).text();
            $(this).text('delete_forever');
            $(this).one('mouseout', function() {
                $(this).text(symbl);
            });
        });
    }
    if(hotreload_part === 'stat' || hotreload_part === ''){
        // STATS
        let us = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'statistics'
        }
        await $.ajax({
            url: '/_api/sconn/servermodel',
            type: 'POST',
            data: JSON.stringify(us),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                $('#cardHolderStats')[0].innerHTML = '';
                $('#cardHolderStats')[0].innerHTML += `
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th scope="col">#</th>
                                <th scope="col">broker</th>
                                <th scope="col">entity type</th>
                                <th scope="col">entity id</th>
                                <th scope="col">details</th>
                                <th scope="col">timestamp</th>
                            </tr>
                        </thead>
                        <tbody id="logRows">
                        </tbody>
                    </table>
                `;

                response.answer.forEach(response_row => {
                    $('#logRows')[0].innerHTML += `
                        <tr>
                            <td>${response_row.id}</td>
                            <td>${response_row.broker}</td>
                            <td>${response_row.entitytype}</td>
                            <td>${response_row.entityid}</td>
                            <td>${response_row.teltx}</td>
                            <td>${response_row.created}</td>
                        </tr> 
                    `;
                });

                console.log(response)
            },
            error: function(xhr, status, error) {
                $('#cardHolderStats')[0].innerHTML = '<p class="work-sans-lite">Unable to retrieve logs from server.</p>';
                console.error('Error:', xhr.responseText);
            }
        });
    }

    await $('.o_cam_card').each(function() {
        let camCard = this;
        let dt = {
            "serverid": $('#serverid')[0].value,
            "entitytype": "camera",
            "action": "open",
            "mainid": "DODA_cam_"+camCard.id.split('_')[3],
            "secondaryid":'1'
        }
        $.ajax({
            url: '/_api/sconn/assign',
            type: 'POST',
            data: JSON.stringify(dt),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                if(response == null){
                    $(camCard).find('.card-text')[0].innerHTML = 'operation timed out';
                }else if(response.code === '200'){
                    $(camCard).find('.card-text')[0].innerHTML = '<img class="img-fluid" src="data:image/webp;base64,'+response.answer+'" alt="camera image" />';
                }else{
                    $(camCard).find('.card-text')[0].innerHTML = response.answer;
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseText);
            }
        })
    });
}

$(document).ready(function() {
    sleep(1000).then(() => {main('');});
});
