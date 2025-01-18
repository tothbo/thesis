function sleep (time){return new Promise((resolve) => setTimeout(resolve, time))}
var server_color = $('#server_color')[0].value;
function colorCorrect(new_id){
    if(new_id === '' || new_id === null || new_id === undefined){
        return server_color
    }
    return new_id
}
function group_calc(key, numpl) {
    let ret = '';
    if (key) {
        ret += `
            <span class="material-symbols-outlined col-1">
                vpn_key
            </span>
            <span class="work-sans-lite col-3">key on</span>
        `;
    } else {
        ret += `
            <span class="material-symbols-outlined col-1">
                vpn_key_off
            </span>
            <span class="work-sans-lite col-3">key off</span>
        `;
    }
    if (numpl) {
        ret += `
            <span class="material-symbols-outlined col-1">
                pin
            </span>
            <span class="work-sans-lite col-6">numplate on</span>
        `;
    } else {
        ret += `
            <span class="material-symbols-outlined col-1">
                credit_card_off
            </span>
            <span class="work-sans-lite col-6">numplate off</span>
        `;
    }
    return ret
}
async function disable_settings(enable_only){
    if($(".sett-disable.disabled").length === $(".sett-disable").length && !enable_only){
        $('.sett-disable').removeClass('disabled');
        $('#cardHolderDoors').on('mouseover', '.remove-icon', function() {
            let symbl = $(this).text();
            $(this).text('delete_forever');
            $(this).one('mouseout', function() {
                $(this).text(symbl);
            });
        });
        $('#cardHolderUsers').on('mouseover', '.remove-icon', function() {
            let symbl = $(this).text();
            $(this).text('delete_forever');
            $(this).one('mouseout', function() {
                $(this).text(symbl);
            });
        });
        $('#cardHolderNumPlates').on('mouseover', '.remove-icon', function() {
            let symbl = $(this).text();
            $(this).text('delete_forever');
            $(this).one('mouseout', function() {
                $(this).text(symbl);
            });
        });
        $('#cardHolderPermGroups').on('mouseover', '.remove-icon', function() {
            let symbl = $(this).text();
            $(this).text('delete_forever');
            $(this).one('mouseout', function() {
                $(this).text(symbl);
            });
        });
    }else{
        $('.sett-disable').addClass('disabled');
        $('#cardHolderDoors').off('mouseover', '.remove-icon');
        $('#cardHolderUsers').off('mouseover', '.remove-icon');
        $('#cardHolderNumPlates').off('mouseover', '.remove-icon');
        $('#cardHolderPermGroups').off('mouseover', '.remove-icon');
    }  
}

// functional queries
async function remove_card(itemtype, itemid){
    if($(".sett-disable.disabled").length === $(".sett-disable").length){return}
    let dt = {
        'serverid':$('#serverid')[0].value,
        'entitytype':itemtype,
        'entityid':itemid,
        'action':'remove',
        'extra':''
    }
    let cont = false;
    await $.ajax({
        url: '/_api/sconn/entitymodel',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            console.log(response);
            cont = true;
        },
        error: function(xhr, status, error) {
            $('#cardHolderDoors')[0].innerHTML = `exception happened while communicating with server, please try again later`;
            console.error('Error:', xhr.responseText);
        }
    });
    if(itemtype === 'door' && cont){$('#cardHolderDoors')[0].innerHTML = `<div class="spinner-grow text-primary" role="status"><span class="visually-hidden">Loading...</span></div>`;main('doors');}
    else if(itemtype === 'user' && cont){$('#cardHolderUsers')[0].innerHTML = `<div class="spinner-grow text-primary" role="status"><span class="visually-hidden">Loading...</span></div>`;main('users');}
    else if(itemtype === 'numberplate' && cont){$('#cardHolderNumPlates')[0].innerHTML = `<div class="spinner-grow text-primary" role="status"><span class="visually-hidden">Loading...</span></div>`;main('numplates');}
    else if(itemtype === 'permission' && cont){$('#cardHolderPermGroups')[0].innerHTML = `<div class="spinner-grow text-primary" role="status"><span class="visually-hidden">Loading...</span></div>`;main('permgroups');}
}


async function remote_open(doorid){
    $('#remoteOpenText')[0].classList.remove('btn-outline-success');
    $('#remoteOpenText')[0].classList.add('btn-outline-secondary');
    $('#remoteOpenText')[0].innerHTML = 'connecting to door...';
    let dt = {
        "serverid": $('#serverid')[0].value,
        "entitytype": "user",
        "action": "open",
        "mainid": doorid,
        "secondaryid":'1'
    }
    $.ajax({
        url: '/_api/sconn/assign',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            console.log(response);
            if(response.answer === 'SUCCESS'){
                $('#remoteOpenText')[0].classList.add('btn-outline-success');
                $('#remoteOpenText')[0].classList.remove('btn-outline-secondary');
                $('#remoteOpenText')[0].innerHTML = 'youre in!';
                sleep(3000).then(() => {
                    $('#remoteOpen').modal('hide');
                    return;
                });
            }else{
                $('#remoteOpenText')[0].classList.add('btn-outline-danger');
                $('#remoteOpenText')[0].classList.remove('btn-outline-secondary');
                $('#remoteOpenText')[0].innerHTML = 'error happened, maybe the door is unreachable?';
                sleep(3000).then(() => {
                    $('#remoteOpen').modal('hide');
                    return;
                });
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
        }
    });
}

async function regNFC(stat, userid, username){
    if(stat === 0){
        $('#regNFCStart').removeClass();
        $('#regNFCStart')[0].disabled = false;
        $('#regNFCStart')[0].classList.add('work-sans-fnt');
        $('#regNFCStart')[0].classList.add('btn');
        $('#regNFCStart')[0].classList.add('btn-primary');
        $('#regNFCStart')[0].innerHTML = 'start';
        $('#regNFCUserId')[0].value = userid;
        $('#regNFCUser')[0].innerHTML = username;
        return;
    }
    $('#regNFCStart')[0].disabled = true;
    $('#regNFCStart')[0].classList.add('btn-outline-secondary');
    $('#regNFCStart')[0].classList.remove('btn-primary');
    $('#regNFCStart')[0].innerHTML = 'communicating with door...';
    userid = $('#regNFCUserId')[0].value;
    let doorid = $('#regNFCDoorSelector')[0].value;
    let dt = {
        "serverid": $('#serverid')[0].value,
        "entitytype": "user",
        "action": "register",
        "mainid": userid,
        "secondaryid": doorid
    }
    $.ajax({
        url: '/_api/sconn/assign',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            console.log(response);
            if(response.answer === 'SUCCESS'){
                $('#regNFCStart')[0].classList.add('btn-outline-success');
                $('#regNFCStart')[0].classList.remove('btn-outline-secondary');
                $('#regNFCStart')[0].innerHTML = 'success, please wait...';
                main('users');
                disable_settings();
                sleep(3000).then(() => {
                    $('#regNFC').modal('hide');
                    return;
                });
            }else{
                $('#regNFCStart')[0].classList.add('btn-outline-danger');
                $('#regNFCStart')[0].classList.remove('btn-outline-secondary');
                $('#regNFCStart')[0].innerHTML = 'error happened, maybe you havent touched the card?';
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
        }
    });
}

async function permgroup_addrem(cardid,secid){
    let entype = 'door'
    let actype = 'assign'

    if(cardid.includes('doorcard')){entype = 'door'}
    else if(cardid.includes('usercard')){entype = 'user'}
    else if(cardid.includes('numplatecard')){entype = 'numberplate'}

    let permid = $('.text-bg-secondary')[0].id.split('_')[1]
    
    if($('#'+cardid)[0].classList.contains('text-bg-warning') === true){
        actype = 'revoke'
        $('#'+cardid).removeClass('text-bg-warning');
        $('#'+cardid).find('.permgroup-add').removeClass('d-none');
        $('#'+cardid).find('.permgroup-rem').addClass('d-none');
    }else{
        $('#'+cardid).addClass('text-bg-warning');
        $('#'+cardid).find('.permgroup-add').addClass('d-none');
        $('#'+cardid).find('.permgroup-rem').removeClass('d-none');
    }


    let dt = {
        "serverid": $('#serverid')[0].value,
        "entitytype": entype,
        "action": actype,
        "mainid": permid,
        "secondaryid": secid
    }
    $.ajax({
        url: '/_api/sconn/assign',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            console.log(response);
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
        }
    });
}

async function permgroup_assign(cardid, permid, wo){
    await $('#'+cardid).find('.btn-warning').addClass('disabled');
    await disable_settings();
    await $('#'+cardid).find('.btn-warning').removeClass('disabled');
    if($('#'+cardid)[0].classList.contains('text-bg-secondary') === false){
        $('#'+cardid)[0].classList.add('text-bg-secondary');
        console.log(cardid);
        $(".perm-selector").removeClass("d-none");
        let dt = {
            'serverid':$('#serverid')[0].value,
            'entityid':permid,
            'action':'get',
            'entitytype':'permission',
            'extra':''
        }
        $.ajax({
            url: '/_api/sconn/entitymodel',
            type: 'POST',
            data: JSON.stringify(dt),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                console.log(response);
                response.answer.doors.forEach((id) => {
                    $('#doorcard_'+id).addClass('text-bg-warning');
                    $('#doorcard_'+id).find('.permgroup-add').addClass('d-none');
                    $('#doorcard_'+id).find('.permgroup-rem').removeClass('d-none');
                });
                response.answer.users.forEach((id) => {
                    $('#usercard_'+id).addClass('text-bg-warning');
                    $('#usercard_'+id).find('.permgroup-add').addClass('d-none');
                    $('#usercard_'+id).find('.permgroup-rem').removeClass('d-none');
                });
                response.answer.numplates.forEach((id) => {
                    $('#numplatecard_'+id).addClass('text-bg-warning');
                    $('#numplatecard_'+id).find('.permgroup-add').addClass('d-none');
                    $('#numplatecard_'+id).find('.permgroup-rem').removeClass('d-none');
                });
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseText);
            }
        });
        return
    }
    $('.permgroup-add').removeClass('d-none');
    $('.permgroup-rem').addClass('d-none');
    $('.text-bg-warning').removeClass('text-bg-warning');
    $('.text-bg-secondary').removeClass('text-bg-secondary');
    $(".perm-selector").addClass("d-none");
}

async function qr_gen(userid){
    let dt = {
        'serverid':$('#serverid')[0].value,
        'entityid':userid,
        'action':'get',
        'entitytype':'user',
        'extra':'req_qr_data'
    }
    $('#showQRCode')[0].innerHTML = '';
    $.ajax({
        url: '/_api/sconn/entitymodel',
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
            $('#showQRCodeFor')[0].innerHTML = response.answer.name;
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
        }
    });
} 

async function new_user(backways){
    disable_settings();
    if(backways === undefined || backways === false){
        $('#cardNewUser')[0].classList.add('d-none');
        $('#cardHolderUsers')[0].innerHTML = `
            <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${colorCorrect()}" id="usercard_new">
                <div class="card-body" style="min-width: 20rem;">
                    <h5 class="card-title row gap-1">
                        <span class="col-6 fst-italic">new</span>
                        <a onclick="user_sett('usercard_new', 'new',true);" class="btn btn-primary col-2 card-sett" style="background-color:${colorCorrect()};border-color:${colorCorrect()};font-size:0.5rem;">save</a>
                        <a onclick="new_user(true);" class="btn btn-secondary mr-1 col-2 card-sett" style="font-size:0.5rem;">cancel</a>
                        <span class="material-symbols-outlined col-1">
                            vpn_key
                        </span>
                    </h5>
                    <p class="card-text">
                        <form class="col-12">
                            <div class="mb-2">
                                <label for="userSettingsInputName" class="form-label">name</label>
                                <input type="text" class="form-control" id="userSettingsInputName" value="" />
                            </div>
                        </form>
                    </p>
                </div>
            </div>
        ` + $('#cardHolderUsers')[0].innerHTML;
        return
    }
    $('#cardNewUser')[0].classList.remove('d-none');
    $('#usercard_new').remove();
}

async function new_numplate(backways){
    disable_settings();
    if(backways === undefined || backways === false){
        $('#cardNewNumPlate')[0].classList.add('d-none');
        $('#cardHolderNumPlates')[0].innerHTML = `
            <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${colorCorrect()}" id="numplatecard_new">
                <div class="card-body" style="min-width: 20rem;">
                    <h5 class="card-title row gap-1">
                        <span class="col-6 fst-italic">new</span>
                        <a onclick="numplate_sett('numplatecard_new','new',true);" class="btn btn-primary col-2 card-sett" style="background-color:${colorCorrect()};border-color:${colorCorrect()};font-size:0.5rem;">save</a>
                        <a onclick="new_numplate(true);" class="btn btn-secondary mr-1 col-2 card-sett" style="font-size:0.5rem;">cancel</a>
                        <span class="material-symbols-outlined col-1">
                            pin
                        </span>
                    </h5>
                    <p class="card-text">
                        <form class="col-12">
                            <div class="mb-2">
                                <label for="numplateSettingsInputNumplate" class="form-label">number plate</label>
                                <input type="text" class="form-control" id="numplateSettingsInputNumplate" value="" />
                            </div>
                            <div class="mb-2">
                                <label for="numplateSettingsInputNickname" class="form-label">nickname</label>
                                <input type="text" class="form-control" id="numplateSettingsInputNickname" value="" />
                            </div>
                        </form>
                    </p>
                </div>
            </div>
        ` + $('#cardHolderNumPlates')[0].innerHTML;
        return
    }
    $('#cardNewNumPlate')[0].classList.remove('d-none');
    $('#numplatecard_new').remove();
}

async function new_permgroup(backways){
    disable_settings();
    if(backways === undefined || backways === false){
        $('#cardNewPermGroup')[0].classList.add('d-none');
        $('#cardHolderPermGroups')[0].innerHTML = `
            <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${colorCorrect()}" id="permgroupcard_new">
                <div class="card-body" style="min-width: 20rem;">
                    <h5 class="card-title row gap-1">
                        <span class="col-6 fst-italic">new</span>
                        <a onclick="permgroup_sett('permgroupcard_new','new',true);" class="btn btn-primary col-2 card-sett" style="background-color:${colorCorrect()};border-color:${colorCorrect()};font-size:0.5rem;">save</a>
                        <a onclick="new_permgroup(true);" class="btn btn-secondary mr-1 col-2 card-sett" style="font-size:0.5rem;">cancel</a>
                        <span class="material-symbols-outlined col-1">
                            pin
                        </span>
                    </h5>
                    <p class="card-text">
                        <form class="col-12">
                            <div class="mb-2">
                                <label for="permgroupSettingsInputGroupName" class="form-label">group name</label>
                                <input type="text" class="form-control" id="permgroupSettingsInputGroupName" value="" />
                            </div>
                            <div class="mb-2 row">
                                <div class="col-4">
                                    <div class="form-check form-switch form-switch-lg">
                                        <label class="form-check-label" for="permgroupSettingsInputKeyEnabled">
                                            key
                                        </label>
                                        <input class="form-check-input oneway_checkbox" type="checkbox" value='a' role="switch" id="permgroupSettingsInputKeyEnabled" />
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="form-check form-switch form-switch-lg">
                                        <label class="form-check-label" for="permgroupSettingsInputNumplateEnabled">
                                            numplate
                                        </label>
                                        <input class="form-check-input oneway_checkbox" type="checkbox" value='a' role="switch" id="permgroupSettingsInputNumplateEnabled" />
                                    </div>
                                </div>
                            </div>
                        </form>
                    </p>
                </div>
            </div>
        ` + $('#cardHolderPermGroups')[0].innerHTML;
        return
    }
    $('#cardNewPermGroup')[0].classList.remove('d-none');
    $('#permgroupcard_new').remove();
}


async function auth_door(card_id, door_id, color, auth_forw){
    let a = $('#'+card_id)[0];
    $(a).find('.btn-primary')[0].classList.add('d-none');
    $(a).find('.card-text')[0].innerHTML = "<div class='spinner-grow text-primary' style='background-color:"+color+"' role='status'><span class='visually-hidden'>Loading...</span></div>";
    await sleep(1000);
    let auth_type = 'add'
    if(auth_forw){
        auth_type = 'remove'
    }
    let dt = {
        'serverid':$('#serverid')[0].value,
        'entitytype':'door',
        'entityid':door_id,
        'action':auth_type,
        'extra':''
    }
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
        }
    });
    $('#cardHolderDoors')[0].innerHTML = `<div class="spinner-grow text-primary" role="status"><span class="visually-hidden">Loading...</span></div>`;
    main('doors');
}

async function door_sett(card_id, door_id, color, process_data){
    disable_settings();
    let a = $('#'+card_id)[0];
    let dt = {
        'serverid':$('#serverid')[0].value,
        'entitytype':'door',
        'entityid':door_id,
        'action':'get',
        'extra':''
    }
    if(process_data){
        dt = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'door',
            'entityid':door_id,
            'action':'modify',
            'extra':{
                'nickname':$(a).find('#doorSettingsInputNickname')[0].value,
                'location':$(a).find('#doorSettingsInputLocation')[0].value,
                'color':$(a).find('#doorSettingsInputColor')[0].value,
                'camera_link':$(a).find('#doorSettingsInputCamlink')[0].value
            }
        }
        $(a)[0].classList.remove('card-open');
    }

    $(a).find('.card-text')[0].innerHTML = "<div class='spinner-grow text-primary' style='background-color:"+color+"' role='status'><span class='visually-hidden'>Loading...</span></div>";

    let resp = null;

    // get new data / submit modifications
    await sleep(1000);
    await $.ajax({
        url: '/_api/sconn/entitymodel',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            console.log(response);
            if($(a)[0].classList.contains('card-open')){
                $(a)[0].classList.remove('card-open');
                $(a).find('.card-sett')[0].classList.add('d-none');
                $(a).find('.card-norm')[0].classList.remove('d-none');
                $(a).find('.card-text')[0].innerHTML = `
                    <span class="col-7 card-mn">${response.answer.location}</span>
                `;
                return
            }
            resp = response;
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            $(a).find('.card-text')[0].innerHTML = 'Cant load settings - exception happened in the request';
            process_data = false
        }
    });

    if(resp){
        dt = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'camera'
        }

        await $.ajax({
            url: '/_api/sconn/servermodel',
            type: 'POST',
            data: JSON.stringify(dt),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                console.log(response);

                $(a)[0].classList.add('card-open');
                $(a).find('.card-sett')[0].classList.remove('d-none');
                $(a).find('.card-norm')[0].classList.add('d-none');
                $(a).find('.card-text')[0].innerHTML = `
                    <form class="col-12">
                        <div class="mb-2">
                            <label for="doorSettingsInputNickname" class="form-label">nickname</label>
                            <input type="text" class="form-control" id="doorSettingsInputNickname" value="${resp.answer.nickname}" />
                        </div>
                        <div class="mb-2">
                            <label for="doorSettingsInputLocation" class="form-label">location</label>
                            <input type="text" class="form-control" value="${resp.answer.location}" id="doorSettingsInputLocation" />
                        </div>
                        <div class="mb-2">
                            <div class="row">
                                <div class="col-2">
                                    <label for="doorSettingsInputColor" class="form-label">color</label>
                                    <input type="color" class="form-control form-control-color" title="choose a custom color" value="${resp.answer.color}" id="doorSettingsInputColor">
                                </div>
                                <div class="col-10">
                                    <label for="doorSettingsInputCamlink" class="form-label">camera link</label>
                                    <select class="form-select form-control" id="doorSettingsInputCamlink">
                                        <option value="">- none -</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </form>
                `;

                response.answer.forEach(row => {
                    if (resp.answer.camera_link === row.local_correlid){
                        $(a).find('#doorSettingsInputCamlink').append(`<option value="${row.local_correlid}" selected>${row.rtsp_host.split('/')[2]}</option>`);
                    }else{
                        $(a).find('#doorSettingsInputCamlink').append(`<option value="${row.local_correlid}">${row.rtsp_host.split('/')[2]}</option>`);
                    }
                });
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseText);
                $(a).find('.card-text')[0].innerHTML = 'Cant load settings - exception happened in the request';
                process_data = false
            }
        });
    }

    if(process_data){$('#cardHolderDoors')[0].innerHTML = `<div class="spinner-grow text-primary" role="status"><span class="visually-hidden">Loading...</span></div>`;main('doors');}
}

async function user_sett(card_id,local_userid,process_data){
    disable_settings()
    let a = $('#'+card_id)[0];
    let dt = {
        'serverid':$('#serverid')[0].value,
        'entitytype':'user',
        'entityid':local_userid,
        'action':'get',
        'extra':'req_user_list'
    }
    if(process_data && local_userid !== 'new'){ 
        dt = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'user',
            'entityid':local_userid,
            'action':'modify',
            'extra':{
                'name':$(a).find('#userSettingsInputName')[0].value,
                'global_userid':$(a).find('#userSettingsInputGlobalid')[0].value
            }
        }
        if($(a).find('#userSettingsInputFid')[0].checked === false){
            dt.extra.fid = null
        }
        $(a)[0].classList.remove('card-open');
    }else if(process_data && local_userid === 'new'){
        dt = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'user',
            'entityid':$(a).find('#userSettingsInputName')[0].value,
            'action':'add',
            'extra':{
                'global_userid':$(a).find('#userSettingsInputName')[0].value
            }
        }
    }

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
            if($(a)[0].classList.contains('card-open')){
                $(a)[0].classList.remove('card-open');
                $(a).find('.card-sett')[0].classList.add('d-none');
                $(a).find('.card-sett')[1].classList.add('d-none');
                $(a).find('.card-norm')[0].classList.remove('d-none');
                $(a).find('.card-text')[0].innerHTML = `
                    <span class="col-7 card-mn">last modified at ${response.answer.last_logged}</span>
                `;
                return
            }
            $(a)[0].classList.add('card-open');
            $(a).find('.card-sett')[0].classList.remove('d-none');
            $(a).find('.card-sett')[1].classList.remove('d-none');
            $(a).find('.card-norm')[0].classList.add('d-none');
            var chk = 'disabled'
            if(response.answer.fid === true){
                chk = 'checked'
            }
            var qrbtn = ''
            if(response.answer.global_userid === null || response.answer.global_userid === ''){
                qrbtn = 'd-none'
            }
            $(a).find('.card-text')[0].innerHTML = `
                <form class="col-12">
                    <div class="mb-2">
                        <label for="userSettingsInputName" class="form-label">name</label>
                        <input type="text" class="form-control" id="userSettingsInputName" value="${response.answer.name}" />
                    </div>
                    <div class="mb-2">
                        <label for="userSettingsInputGlobalid" class="form-label">global user id</label>
                        <select class="form-select work-sans-lite" aria-label="Global user id selector" id="userSettingsInputGlobalid">
                          <option value="">- none -</option>
                        </select>
                    </div>
                    <div class="mb-2 row">
                        <div class="col-5">
                            <div class="form-check form-switch form-switch-lg">
                                <label class="form-check-label" for="userSettingsInputFid">
                                    face auth 
                                </label>
                                <input class="form-check-input oneway_checkbox" type="checkbox" value='a' role="switch" id="userSettingsInputFid" ${chk}>
                            </div>
                        </div>
                        <div class="col-3">
                            <a onclick="qr_gen('${response.answer.local_userid}');" class="btn btn-outline-secondary btn-user ${qrbtn}" id="userSettingsCheckDynunq" data-bs-toggle="modal" data-bs-target="#showQR">test qr</a>
                        </div>
                        <div class="col-4">
                            <a onclick="regNFC(0, '${response.answer.local_userid}', '${response.answer.name}');" class="btn btn-outline-secondary btn-user" id="userSettingsRegisterNFC" data-bs-toggle="modal" data-bs-target="#regNFC">connect card</a>
                        </div>
                    </div>
                </form>
            `;

            response.userlist.forEach(row => {
                if (response.answer.global_userid === row.global_userid){
                    $(a).find('#userSettingsInputGlobalid').append(`<option value="${row.global_userid}" selected>${row.global_userid}</option>`);
                }else{
                    $(a).find('#userSettingsInputGlobalid').append(`<option value="${row.global_userid}">${row.global_userid}</option>`);
                }
            });
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            $(a).find('.card-text')[0].innerHTML = 'Cant load settings - exception happened in the request';
            process_data = false
        }
    });
    if(process_data){$('#cardHolderUsers')[0].innerHTML = `<div class="spinner-grow text-primary" role="status"><span class="visually-hidden">Loading...</span></div>`;main('users');}
}

async function numplate_sett(card_id, numplateid, process_data){
    disable_settings()
    let a = $('#'+card_id)[0];
    var dt = {
        'serverid':$('#serverid')[0].value,
        'entitytype':'numberplate',
        'entityid':numplateid,
        'action':'get',
        'extra':''
    }
    if(process_data && numplateid !== 'new'){ 
        dt = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'numberplate',
            'entityid':numplateid,
            'action':'modify',
            'extra':{
                'numplate':$(a).find('#numplateSettingsInputNumplate')[0].value.toUpperCase(),
                'nickname':$(a).find('#numplateSettingsInputNickname')[0].value
            }
        }
        $(a)[0].classList.remove('card-open');
    }else if(process_data && numplateid === 'new'){
        dt = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'numberplate',
            'entityid':$(a).find('#numplateSettingsInputNumplate')[0].value.toUpperCase(),
            'action':'add',
            'extra':{
                'nickname':$(a).find('#numplateSettingsInputNickname')[0].value
            }
        }
    }

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
            if($(a)[0].classList.contains('card-open')){
                $(a)[0].classList.remove('card-open');
                $(a).find('.card-sett')[0].classList.add('d-none');
                $(a).find('.card-sett')[1].classList.add('d-none');
                $(a).find('.card-norm')[0].classList.remove('d-none');
                $(a).find('.card-text')[0].innerHTML = `
                    <span class="col-7 card-mn">${response.answer.nickname}<br/>last modified at ${response.answer.last_logged}</span>
                `;
                return
            }
            $(a)[0].classList.add('card-open');
            $(a).find('.card-sett')[0].classList.remove('d-none');
            $(a).find('.card-sett')[1].classList.remove('d-none');
            $(a).find('.card-norm')[0].classList.add('d-none');
            $(a).find('.card-text')[0].innerHTML = `
                <form class="col-12">
                    <div class="mb-2">
                        <label for="numplateSettingsInputNumplate" class="form-label">number plate</label>
                        <input type="text" class="form-control" id="numplateSettingsInputNumplate" value="${response.answer.numplate}" />
                    </div>
                    <div class="mb-2">
                        <label for="numplateSettingsInputNickname" class="form-label">nickname</label>
                        <input type="text" class="form-control" id="numplateSettingsInputNickname" value="${response.answer.nickname}" />
                    </div>
                </form>
            `;
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            $(a).find('.card-text')[0].innerHTML = 'Cant load settings - exception happened in the request';
            process_data = false
        }
    });
    if(process_data){$('#cardHolderNumPlates')[0].innerHTML = `<div class="spinner-grow text-primary" role="status"><span class="visually-hidden">Loading...</span></div>`;main('numplates');}
}


async function permgroup_sett(card_id, permid, process_data){
    disable_settings()
    let a = $('#'+card_id)[0];
    var dt = {
        'serverid':$('#serverid')[0].value,
        'entitytype':'permission',
        'entityid':permid,
        'action':'get',
        'extra':''
    }
    if(process_data && permid !== 'new'){ 
        dt = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'permission',
            'entityid':permid,
            'action':'modify',
            'extra':{
                'group_name':$(a).find('#permgroupSettingsInputGroupName')[0].value,
                'user_enabled':$(a).find('#permgroupSettingsInputKeyEnabled')[0].checked,
                'numplate_enabled':$(a).find('#permgroupSettingsInputNumplateEnabled')[0].checked
            }
        }
        $(a)[0].classList.remove('card-open');
    }else if(process_data && permid === 'new'){
        dt = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'permission',
            'entityid':$(a).find('#permgroupSettingsInputGroupName')[0].value,
            'action':'add',
            'extra':{
                'user_enabled':$(a).find('#permgroupSettingsInputKeyEnabled')[0].checked,
                'numplate_enabled':$(a).find('#permgroupSettingsInputNumplateEnabled')[0].checked
            }
        }
    }

    $(a).find('.card-text')[0].innerHTML = "<div class='ml-5'><div class='spinner-grow text-primary' style='background-color:"+server_color+"' role='status'><span class='visually-hidden'>Loading...</span></div></div>";

    // get new data / submit modifications
    await sleep(1000);
    await $.ajax({
        url: '/_api/sconn/entitymodel',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            console.log(response);
            if($(a)[0].classList.contains('card-open')){
                $(a)[0].classList.remove('card-open');
                $(a).find('.card-sett')[0].classList.add('d-none');
                $(a).find('.card-sett')[1].classList.add('d-none');
                $(a).find('.card-norm')[0].classList.remove('d-none');
                $(a).find('.card-norm')[1].classList.remove('d-none');
                $(a).find('.card-text')[0].innerHTML = group_calc(response.answer.user_enabled,response.answer.numplate_enabled);
                return
            }
            $(a)[0].classList.add('card-open');
            $(a).find('.card-sett')[0].classList.remove('d-none');
            $(a).find('.card-sett')[1].classList.remove('d-none');
            $(a).find('.card-norm')[0].classList.add('d-none');
            $(a).find('.card-norm')[1].classList.add('d-none');
            let chk_num = ''
            let chk_key = ''
            if(response.answer.numplate_enabled === true){
                chk_num = 'checked'
            }
            if(response.answer.user_enabled === true){
                chk_key = 'checked'
            }
            $(a).find('.card-text')[0].innerHTML = `
                <form class="col-12">
                    <div class="mb-2">
                        <label for="permgroupSettingsInputGroupName" class="form-label">group name</label>
                        <input type="text" class="form-control" id="permgroupSettingsInputGroupName" value="${response.answer.group_name}" />
                    </div>
                    <div class="mb-2 row">
                        <div class="col-4">
                            <div class="form-check form-switch form-switch-lg">
                                <label class="form-check-label" for="permgroupSettingsInputKeyEnabled">
                                    key
                                </label>
                                <input class="form-check-input oneway_checkbox" type="checkbox" value='a' role="switch" id="permgroupSettingsInputKeyEnabled" ${chk_key}>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="form-check form-switch form-switch-lg">
                                <label class="form-check-label" for="permgroupSettingsInputNumplateEnabled">
                                    numplate
                                </label>
                                <input class="form-check-input oneway_checkbox" type="checkbox" value='a' role="switch" id="permgroupSettingsInputNumplateEnabled" ${chk_num}>
                            </div>
                        </div>
                    </div>
                </form>
            `;
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            $(a).find('.card-text')[0].innerHTML = 'Cant load settings - exception happened in the request';
            process_data = false
        }
    });
    if(process_data){$('#cardHolderPermGroups')[0].innerHTML = `<div class='ml-5'><div class='spinner-grow text-primary' role='status'><span class='visually-hidden'>Loading...</span></div></div>`;main('permgroups');}
}



//// MAIN

async function main(hotreload_part){
    // DOOR
    if(hotreload_part === 'doors' || hotreload_part === ''){
        let dt = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'door'
        }
        await $.ajax({
            url: '/_api/sconn/servermodel',
            type: 'POST',
            data: JSON.stringify(dt),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                if(response === null){
                    $('#cardHolderDoors')[0].innerHTML = '<p class="work-sans-lite">connection with server lost, maybe its offline?!</p>';
                    return;
                }
                $('#cardHolderDoors')[0].innerHTML = '';
                $('#regNFCDoorSelector')[0].innerHTML = '';
                response.answer.forEach(sdata => {
                    console.log(sdata);
                    if(sdata.authorized){
                        // row view
                        $('#cardHolderDoors')[0].innerHTML += `
                            <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${colorCorrect(sdata.color)}" id="doorcard_${sdata.local_correlid}">
                                <div class="card-body" style="min-width: 20rem;">
                                    <h5 class="card-title row">
                                        <span class="col-10">${sdata.nickname}</span>
                                        <a href="#" onclick="javascript:remove_card('door','${sdata.local_correlid}');" class="material-symbols-outlined remove-icon sett-disable col-1" style="text-decoration: none;color:${colorCorrect(sdata.color)}!important;">
                                            room_preferences
                                        </a>
                                    </h5>
                                    <p class="card-text">
                                        <span class="col-7 card-mn">${sdata.location}</span>
                                    </p>
                                    <div class="card-sett d-none">
                                        <a onclick="door_sett('doorcard_${sdata.local_correlid}','${sdata.local_correlid}','${colorCorrect(sdata.color)}', true);" class="btn btn-primary btn-main col-3 fader" style="background-color:${colorCorrect(sdata.color)} !important;border-color:${colorCorrect(sdata.color)} !important">save</a>
                                        <a onclick="door_sett('doorcard_${sdata.local_correlid}','${sdata.local_correlid}','${colorCorrect(sdata.color)}');" class="btn btn-secondary btn-sec col-4 fader">cancel</a>
                                        <a onclick="auth_door('doorcard_${sdata.local_correlid}','${sdata.local_correlid}','${colorCorrect(sdata.color)}', true);" class="btn btn-warning col-4 fader">remove</a>
                                    </div>
                                    <div class="card-norm">
                                        <a onclick="remote_open('${sdata.local_correlid}');" class="btn btn-primary btn-main col-3 fader" data-bs-toggle="modal" data-bs-target="#remoteOpen" style="background-color:${colorCorrect(sdata.color)} !important;border-color:${colorCorrect(sdata.color)} !important">open</a>
                                        <a onclick="door_sett('doorcard_${sdata.local_correlid}','${sdata.local_correlid}','${colorCorrect(sdata.color)}');" class="btn btn-secondary btn-sec col-6 fader sett-disable">settings</a>
                                    </div>
                                </div>
                                <div class="card-footer perm-selector mb-0 d-none">
                                    <button class="btn btn-outline-secondary work-sans-lite permgroup-add" onclick="permgroup_addrem('doorcard_${sdata.local_correlid}','${sdata.local_correlid}');">add to group</button>
                                    <button class="btn btn-secondary d-none work-sans-lite permgroup-rem" onclick="permgroup_addrem('doorcard_${sdata.local_correlid}','${sdata.local_correlid}');">remove from group</button>
                                </div>
                            </div>
                        `;
                        $('#regNFCDoorSelector')[0].innerHTML += `<option value="${sdata.local_correlid}">${sdata.nickname}</option>`;
                    }else{
                        // row view
                        $('#cardHolderDoors')[0].innerHTML += `
                            <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${colorCorrect(sdata.color)} !important" id="doorcard_${sdata.local_correlid}">
                                <div class="card-body" style="min-width: 20rem;">
                                    <h5 class="card-title row">
                                        <span class="col-10">${sdata.nickname}</span>
                                        <a href="#" onclick="javascript:remove_card('door','${sdata.local_correlid}');" class="material-symbols-outlined remove-icon sett-disable col-1" style="text-decoration: none;color:${colorCorrect(sdata.color)}!important;">
                                            room_preferences
                                        </a>
                                    </h5>
                                    <p class="card-text">
                                        <span class="col-7">waiting for authorization...</span>
                                    </p>
                                    <button onclick="auth_door('doorcard_${sdata.local_correlid}','${sdata.local_correlid}','${colorCorrect(sdata.color)}', false);" class="btn btn-primary col-6" style="background-color:${colorCorrect(sdata.color)};border-color:${colorCorrect(sdata.color)}">authorize</button>
                                </div>
                            </div>
                        `;
                    }
                });
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseText);
                $('#cardHolderDoors')[0].innerHTML = '';
                $('#cardHolderDoors')[0].innerHTML = 'Error happened whiles getting this information. Please try again later.';
            }
        });
        $('#cardHolderDoors').off('mouseover', '.remove-icon');
        $('#cardHolderDoors').on('mouseover', '.remove-icon', function() {
            let symbl = $(this).text();
            $(this).text('delete_forever');
            $(this).one('mouseout', function() {
                $(this).text(symbl);
            });
        });
    }
    
    if(hotreload_part === 'users' || hotreload_part === ''){
        // USERS
        let us = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'user'
        }
        await $.ajax({
            url: '/_api/sconn/servermodel',
            type: 'POST',
            data: JSON.stringify(us),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                if(response === null){
                    $('#cardHolderUsers')[0].innerHTML = '<p class="work-sans-lite">connection with server lost, maybe its offline?!</p>';
                    return;
                }
                $('#cardHolderUsers')[0].innerHTML = '';
                response.answer.forEach(sdata => {
                    console.log(sdata);
                    let key_symb = 'vpn_key'
                    if(sdata.static_unq === false){
                        key_symb = 'vpn_key_alert';
                    }
                    $('#cardHolderUsers')[0].innerHTML += `
                        <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${colorCorrect(sdata.color)}" id="usercard_${sdata.local_userid}">
                            <div class="card-body" style="min-width: 20rem;">
                                <h5 class="card-title row gap-1">
                                    <span class="col-6">${sdata.name}</span>
                                    <a onclick="user_sett('usercard_${sdata.local_userid}', '${sdata.local_userid}',true);" class="btn btn-primary col-2 card-sett d-none" style="background-color:${colorCorrect(sdata.color)};border-color:${colorCorrect(sdata.color)};font-size:0.5rem;">save</a>
                                    <a onclick="user_sett('usercard_${sdata.local_userid}', '${sdata.local_userid}',false);" class="btn btn-secondary mr-1 col-2 card-sett d-none" style="font-size:0.5rem;">cancel</a>
                                    <a onclick="user_sett('usercard_${sdata.local_userid}', '${sdata.local_userid}',false);" class="btn btn-primary col-4 card-norm sett-disable" style="background-color:${colorCorrect(sdata.color)};border-color:${colorCorrect(sdata.color)};font-size:0.5rem;">modify</a>
                                    <a href="#" onclick="remove_card('user','${sdata.local_userid}');" class="material-symbols-outlined remove-icon sett-disable col-1" style="text-decoration: none;color:${colorCorrect(sdata.color)}!important;">
                                        ${key_symb}
                                    </a>
                                </h5>
                                <p class="card-text">
                                    <span class="col-7">last modified at ${sdata.last_logged}</span>
                                </p>
                            </div>
                            <div class="card-footer perm-selector mb-0 d-none">
                                <button class="btn btn-outline-secondary work-sans-lite permgroup-add" onclick="permgroup_addrem('usercard_${sdata.local_userid}','${sdata.local_userid}');">add to group</button>
                                <button class="btn btn-secondary d-none work-sans-lite permgroup-rem" onclick="permgroup_addrem('usercard_${sdata.local_userid}','${sdata.local_userid}');">remove from group</button>
                            </div>
                        </div>
                    `;
                });
                $('#cardNewUser')[0].classList.remove('d-none');
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseText);
                $('#cardHolderUsers')[0].innerHTML = '';
                $('#cardHolderUsers')[0].innerHTML = 'Error happened whiles getting this information. Please try again later.';
            }
        });
        $('#cardHolderUsers').off('mouseover', '.remove-icon');
        $('#cardHolderUsers').on('mouseover', '.remove-icon', function() {
            let symbl = $(this).text();
            $(this).text('delete_forever');
            $(this).one('mouseout', function() {
                $(this).text(symbl);
            });
        });
    }
    
    if(hotreload_part === 'numplates' || hotreload_part === ''){
        // NUMPLATE
        let np = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'numberplate'
        }
        await $.ajax({
            url: '/_api/sconn/servermodel',
            type: 'POST',
            data: JSON.stringify(np),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                if(response === null){
                    $('#cardHolderNumPlates')[0].innerHTML = '<p class="work-sans-lite">connection with server lost, maybe its offline?!</p>';
                    return;
                }
                $('#cardHolderNumPlates')[0].innerHTML = '';
                response.answer.forEach(sdata => {
                    console.log(sdata);
                    $('#cardHolderNumPlates')[0].innerHTML += `
                        <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${colorCorrect(sdata.color)}" id="numplatecard_${sdata.numplateid}">
                            <div class="card-body" style="min-width: 20rem;">
                                <h5 class="card-title row gap-1">
                                    <span class="col-6">${sdata.numplate}</span>
                                    <a onclick="numplate_sett('numplatecard_${sdata.numplateid}', '${sdata.numplateid}',true);" class="btn btn-primary col-2 card-sett d-none" style="background-color:${colorCorrect(sdata.color)};border-color:${colorCorrect(sdata.color)};font-size:0.5rem;">save</a>
                                    <a onclick="numplate_sett('numplatecard_${sdata.numplateid}', '${sdata.numplateid}',false);" class="btn btn-secondary mr-1 col-2 card-sett d-none" style="font-size:0.5rem;">cancel</a>
                                    <a onclick="numplate_sett('numplatecard_${sdata.numplateid}', '${sdata.numplateid}',false);" class="btn btn-primary col-4 card-norm sett-disable" style="background-color:${colorCorrect(sdata.color)};border-color:${colorCorrect(sdata.color)};font-size:0.5rem;">modify</a>
                                    <a href="#" onclick="javascript:remove_card('numberplate','${sdata.numplateid}');" class="material-symbols-outlined remove-icon sett-disable col-1" style="text-decoration: none;color:${colorCorrect(sdata.color)}!important;">
                                        pin
                                    </a>
                                </h5>
                                <p class="card-text">
                                    <span class="col-7">${sdata.nickname}<br/>last modified at ${sdata.last_logged}</span>
                                </p>
                            </div>
                            <div class="card-footer perm-selector mb-0 d-none">
                                <button class="btn btn-outline-secondary work-sans-lite permgroup-add" onclick="permgroup_addrem('numplatecard_${sdata.numplateid}','${sdata.numplateid}');">add to group</button>
                                <button class="btn btn-secondary d-none work-sans-lite permgroup-rem" onclick="permgroup_addrem('numplatecard_${sdata.numplateid}','${sdata.numplateid}');">remove from group</button>
                            </div>
                        </div>
                    `;
                });
                $('#cardNewNumPlate')[0].classList.remove('d-none');
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseText);
                $('#cardHolderNumPlates')[0].innerHTML = '';
                $('#cardHolderNumPlates')[0].innerHTML = 'Error happened whiles getting this information. Please try again later.';
            }
        });
        $('#cardHolderNumPlates').off('mouseover', '.remove-icon');
        $('#cardHolderNumPlates').on('mouseover', '.remove-icon', function() {
            let symbl = $(this).text();
            $(this).text('delete_forever');
            $(this).one('mouseout', function() {
                $(this).text(symbl);
            });
        });
    }

    if(hotreload_part === 'permgroups' || hotreload_part === ''){
        // PERMGROUP
        let np = {
            'serverid':$('#serverid')[0].value,
            'entitytype':'permission'
        }
        await $.ajax({
            url: '/_api/sconn/servermodel',
            type: 'POST',
            data: JSON.stringify(np),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                if(response === null){
                    $('#cardHolderPermGroups')[0].innerHTML = '<p class="work-sans-lite">connection with server lost, maybe its offline?!</p>';
                    return;
                }
                $('#cardHolderPermGroups')[0].innerHTML = '';
                response.answer.forEach(sdata => {
                    console.log(sdata);
                    $('#cardHolderPermGroups')[0].innerHTML += `
                        <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${colorCorrect(sdata.color)}" id="permgroupcard_${sdata.permid}">
                            <div class="card-body" style="min-width: 20rem;">
                                <h5 class="card-title row gap-1">
                                    <span class="col-6">${sdata.group_name}</span>
                                    <a onclick="permgroup_sett('permgroupcard_${sdata.permid}', '${sdata.permid}',true);" class="btn btn-primary col-2 card-sett d-none" style="background-color:${colorCorrect(sdata.color)};border-color:${colorCorrect(sdata.color)};font-size:0.5rem;">save</a>
                                    <a onclick="permgroup_sett('permgroupcard_${sdata.permid}', '${sdata.permid}',false);" class="btn btn-secondary mr-1 col-2 card-sett d-none" style="font-size:0.5rem;">cancel</a>
                                    <a onclick="permgroup_sett('permgroupcard_${sdata.permid}', '${sdata.permid}',false);" class="btn btn-primary col-2 card-norm sett-disable" style="background-color:${colorCorrect(sdata.color)};border-color:${colorCorrect(sdata.color)};font-size:0.4rem;">modify</a>
                                    <a onclick="permgroup_assign('permgroupcard_${sdata.permid}', '${sdata.permid}');" class="btn btn-warning col-2 card-norm sett-disable" style="font-size:0.5rem;">assign</a>
                                    <a href="#" onclick="javascript:remove_card('permission','${sdata.permid}');" class="material-symbols-outlined remove-icon sett-disable col-1" style="text-decoration: none;color:${colorCorrect(sdata.color)}!important;">
                                        communities
                                    </a>
                                </h5>
                                <p class="card-text row">
                                    ${group_calc(sdata.user_enabled,sdata.numplate_enabled)}
                                </p>
                            </div>
                        </div>
                    `;
                });
                $('#cardNewPermGroup')[0].classList.remove('d-none');
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseText);
                $('#cardHolderPermGroups')[0].innerHTML = '';
                $('#cardHolderPermGroups')[0].innerHTML = 'Error happened whilest getting this information. Please try again later.';
            }
        });
        $('#cardHolderPermGroups').off('mouseover', '.remove-icon');
        $('#cardHolderPermGroups').on('mouseover', '.remove-icon', function() {
            let symbl = $(this).text();
            $(this).text('delete_forever');
            $(this).one('mouseout', function() {
                $(this).text(symbl);
            });
        });
    }
}

$(document).ready(function() {
    sleep(1000).then(() => {main('');});
});
