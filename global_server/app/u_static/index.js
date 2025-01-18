function sleep (time){return new Promise((resolve) => setTimeout(resolve, time))}

function chcorrect(input){
    if(input){return 'checked'}
    return ''
}

async function change_pass(open){
    let pass_a = $('#settingsModalPasswd');
    let pass_b = $('#settingsModalRePasswd');

    if(open){
        pass_a[0].value = '';
        pass_b[0].value = '';
        pass_a.removeClass('is-valid');
        pass_a.removeClass('is-invalid');
        pass_b.removeClass('is-valid');
        pass_b.removeClass('is-invalid');
        $('#settingsModalBtn').removeClass('btn-outline-success');
        $('#settingsModalBtn').addClass('btn-outline-primary');
        return;
    }

    // if already open (check submit values)
    if(pass_a[0].value === pass_b[0].value && pass_a[0].value.length >= 4){
        pass_a.addClass('is-valid');
        pass_b.addClass('is-valid');

        let dt = {
            "password": pass_a[0].value
        }

        await $.ajax({
            url: '/_api/passchange',
            type: 'POST',
            data: JSON.stringify(dt),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                console.log(response);
                if(response) {
                    $('#settingsModalBtn').addClass('btn-outline-success');
                    $('#settingsModalBtn').removeClass('btn-outline-primary');
                    $('#settingsModalBtn')[0].innerHTML = 'saved';
                }
            },
            error: function(xhr, status, error) {
                console.log(xhr.responseText);
            }
        });
        await sleep(2000).then(() => {
            $('#settingsModal').modal('hide');
        });
        return;
    }
    pass_a.addClass('is-invalid');
    pass_b.addClass('is-invalid');
}

async function refresh_userlist(card_id,server_id,color){
    let a = $('#'+card_id).find('.user-names');
    $(a)[0].innerHTML = `<p class="work-sans-fnt mb-0">global users</p><div class='spinner-grow text-primary ml-5 mt-3 mb-3' style='background-color:${color}' role='status'><span class='visually-hidden'>Loading...</span></div>`;
    await sleep(100);

    let dt = {
        "serverid": server_id,
        "action": "get",
        "extra": ""
    }

    await $.ajax({
        url: '/_api/clog/serveruserlist',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            $(a)[0].innerHTML = '<p class="work-sans-fnt mb-0">global users</p>';
            for(let row in response.users){
                $(a)[0].innerHTML += `
                <div class="row user-row">
                    <div class="col-8">
                        <p class="work-sans-lite user-row-userid">${response.users[row].global_userid}</p>
                    </div>
                    <div class="col-2">
                        <div class="form-check form-switch form-switch-lg">
                            <input class="form-check-input user-row-admin" type="checkbox" value='a' role="switch" id="serverSettingsInputAdmin#${response.users[row].global_userid}" ${chcorrect(response.users[row].admin)}>
                        </div>
                    </div>
                    <div class="col-2">
                        <a href="#" onclick="server_remove('${card_id}','${server_id}','${response.color}','${response.users[row].global_userid}');" style="color:${response.color}" onclick=""><span class="material-symbols-outlined">delete</span></a>
                    </div>
                </div>
                `;
            }
            $(a)[0].innerHTML += `
                <div class="row mb-3">
                    <div class="col-10">
                        <input type="email" class="form-control form-control-sm work-sans-lite" name="serverSettingsInputNew" id="serverSettingsInputNew" value="" />
                    </div>
                    <div class="col-2">
                        <a href="#" onclick="server_add('${card_id}','${server_id}','${response.color}');" style="color:${response.color}"><span class="material-symbols-outlined">add</span></a>
                    </div>
                </div>
            `;
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
        }
    });
}


async function server_sett(card_id, server_id, color, save){
    let a = $('#'+card_id)[0];
    let cusers = [];
    let newcolor = $(a).find('#serverSettingsInputColor').val();
    let newname = $(a).find('#serverSettingsInputName').val();

    if($(a).find('.user-row').length > 0){
        let ulistelements = $(a).find('.user-row');
        ulistelements.each(function() {
            cusers.push([$(this).find('.user-row-userid')[0].innerText,$(this).find('.user-row-admin').is(':checked')]);
        });
    }

    let dt = {
        "serverid": server_id,
        "action": "get",
        "extra": ""
    }
    
    $(a).find('.card-settings')[0].classList.add('d-none');
    $(a).find('.card-norm')[0].classList.add('d-none');

    $(a).find('.card-text')[0].innerHTML = "<div class='spinner-grow text-primary' style='background-color:"+color+"' role='status'><span class='visually-hidden'>Loading...</span></div>";
    $(a).find('.card-options')[0].innerHTML = '';
    await sleep(1000);

    await $.ajax({
        url: '/_api/clog/serveruserlist',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: async function(response) {
            console.log(response);
            if($(a)[0].classList.contains('card-open') && save){
                // save
                dt = {
                    "serverid": server_id,
                    "action": "modify",
                    "extra": {
                        "color":newcolor,
                        "nickname":newname,
                        "users":[]
                    }
                };
                if(cusers.length > 0){
                    cusers.forEach(row => {
                        dt.extra.users.push({
                            'userid':row[0],
                            'admin':row[1]
                        })
                    });
                }
                
                $.ajax({
                    url: '/_api/clog/serveruserlist',
                    type: 'POST',
                    data: JSON.stringify(dt),
                    contentType: 'application/json; charset=UTF-8',
                    success: function(response) {
                        if(response){
                            console.log('saved');
                            location.reload();
                        }else{
                            $(a).find('.card-text')[0].innerText = 'exception happened while saving changes';
                            return;
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error('Error:', xhr.responseText);
                        $(a).find('.card-text')[0].innerText = 'exception happened while communicating with the server';
                        return;
                    }
                });
            }
            if($(a)[0].classList.contains('card-open')){
                // close if saved OR if regular close
                $(a).find('.card-norm')[0].classList.remove('d-none');
                $(a).find('.btn-connect')[0].classList.add('disabled');
                $(a).find('.btn-sett')[0].classList.add('disabled');
                $(a).find('.btn-connect')[0].classList.add('placeholder');
                $(a)[0].classList.remove('card-open');

                $.ajax({
                    url: '/_api/clog/get_status',
                    type: 'POST',
                    data: JSON.stringify({'serverid':server_id}),
                    contentType: 'application/json; charset=UTF-8',
                    success: function(response) {
                        if(response){
                            $(a).find('.card-text')[0].innerText = 'ready to connect!';
                            $(a).find('.btn-connect')[0].classList.remove('disabled');
                            $(a).find('.btn-connect')[0].classList.remove('placeholder');
                            $(a).find('.btn-sett')[0].classList.remove('disabled');
                            $(a).find('.btn-connect')[0].innerText = 'connect';
                        }else{
                            $(a).find('.card-text')[0].innerText = 'cant reach server, maybe its offline!?';
                            $(a).find('.btn-sett')[0].classList.remove('disabled');
                        }
                    }
                });
                return
            }
            // open
            $(a)[0].classList.add('card-open');
            $(a).find('.card-text')[0].innerHTML = '';
            $(a).find('.card-settings')[0].classList.remove('d-none');
            $(a).find('.card-options')[0].innerHTML = `
                <form class="col-12">
                    <div class="mb-2">
                        <label for="serverSettingsInputName" class="form-label">name</label>
                        <input type="text" class="form-control" id="serverSettingsInputName" value="${response.name}" />
                    </div>
                    <div class="mb-2">
                        <label for="serverSettingsInputColor" class="form-label">color</label>
                        <input type="color" class="form-control form-control-color" title="choose a custom color" value="${response.color}" id="serverSettingsInputColor">
                    </div>
                    <hr>
                    <div class="mb-0 user-names">
                    </div>
                </form>
                <hr class="mt-0">
            `;
            await refresh_userlist(card_id, server_id, color);
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            $(a).find('.card-text')[0].innerHTML = 'Cant load settings - exception happened in the request';
            process_data = false
        }
    });
}

async function server_leave_action(card_id, server_id, color){
    let a = $('#'+card_id)[0];
    
    $(a).find('.card-settings')[0].classList.add('d-none');
    $(a).find('.card-norm')[0].classList.add('d-none');

    $(a).find('.card-text')[0].innerHTML = "<div class='spinner-grow text-primary' style='background-color:"+color+"' role='status'><span class='visually-hidden'>Loading...</span></div>";
    $(a).find('.card-options')[0].innerHTML = '';
    await sleep(1000);

    $.ajax({
        url: '/_api/clog/leaveserver',
        type: 'POST',
        data: JSON.stringify({'serverid':server_id}),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            if(response){
                location.reload();
                return;
            }
            $(a).find('.card-text')[0].innerHTML = 'exception while saving changes please retry later';
        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            $(a).find('.card-text')[0].innerHTML = 'exception happened while communicating with the server, please try again later'
        } 
    });
}

async function server_leave(card_id, server_id, color){
    let a = $('#'+card_id)[0];
    
    $(a).find('.card-settings')[0].classList.add('d-none');
    $(a).find('.card-norm')[0].classList.add('d-none');

    $(a).find('.card-text')[0].innerHTML = "<div class='spinner-grow text-primary' style='background-color:"+color+"' role='status'><span class='visually-hidden'>Loading...</span></div>";
    $(a).find('.card-options')[0].innerHTML = '';
    await sleep(1000);

    if($(a)[0].classList.contains('card-open')){
        $(a).find('.card-norm')[0].classList.remove('d-none');
        $(a).find('.btn-connect')[0].classList.add('disabled');
        $(a).find('.btn-sett')[0].classList.add('disabled');
        $(a).find('.btn-connect')[0].classList.add('placeholder');
        $(a)[0].classList.remove('card-open');

        $.ajax({
            url: '/_api/clog/get_status',
            type: 'POST',
            data: JSON.stringify({'serverid':server_id}),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                if(response){
                    $(a).find('.card-text')[0].innerText = 'ready to connect!';
                    $(a).find('.btn-connect')[0].classList.remove('disabled');
                    $(a).find('.btn-connect')[0].classList.remove('placeholder');
                    $(a).find('.btn-sett')[0].classList.remove('disabled');
                    $(a).find('.btn-connect')[0].innerText = 'connect';
                }else{
                    $(a).find('.card-text')[0].innerText = 'cant reach server, maybe its offline!?';
                    $(a).find('.btn-sett')[0].classList.remove('disabled');
                }
            }
        });
        return
    }

    $(a)[0].classList.add('card-open');
    $(a).find('.card-text')[0].innerHTML = '';
    $(a).find('.card-settings')[0].classList.remove('d-none');
    $(a).find('.card-options')[0].innerHTML = `
        <div class="row"><div class="col-12"><p class="work-sans-lite">are you sure you want to leave?</p></div></div>
    `;
}

async function server_add(card_id,server_id,color){
    let a = $('#'+card_id)[0];
    let new_id = $('#serverSettingsInputNew')[0].value;
    let dt = {
        "serverid": server_id,
        "action": "add",
        "extra":{
            "userid": new_id
        }
    }
    await $.ajax({
        url: '/_api/clog/serveruserlist',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            if(response){
                console.log("user modification saved");
            }
        }
    });
    refresh_userlist(card_id, server_id, color);
}
async function server_remove(card_id,server_id,color,global_userid){
    let a = $('#'+card_id)[0];
    let dt = {
        "serverid": server_id,
        "action": "remove",
        "extra":{
            "userid": global_userid
        }
    }
    await $.ajax({
        url: '/_api/clog/serveruserlist',
        type: 'POST',
        data: JSON.stringify(dt),
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            if(response){
                console.log("user modification saved");
            }
        }
    });
    refresh_userlist(card_id, server_id, color);
}

async function main(){
    await $.ajax({
        url: '/_api/clog/get_servers_v2',
        type: 'POST',
        contentType: 'application/json; charset=UTF-8',
        success: function(response) {
            $('#cardHolderUserServers')[0].innerHTML = '';
            $('#cardHolderAdminServers')[0].innerHTML = '';
            $('#cardHolderNonAvialableServers')[0].innerHTML = '';
            console.log("OK");
            console.log(response);
            response.user.forEach(sdata => {
                $('#cardHolderUserServers')[0].innerHTML += `
                    <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${sdata.color}" id="srcard_${sdata.global_serverid}">
                        <div class="card-body" style="min-width: 20rem;">
                            <h5 class="card-title">
                                <span class="col-6">${sdata.nickname}</span>
                            </h5>
                            <p class="card-text placeholder-glow">
                                <span class="placeholder col-7"></span>
                            </p>
                            <div class="card-options"></div>
                            <div class="card-settings d-none">
                                <a class="btn btn-warning col-4" onclick="server_leave_action('srcard_${sdata.global_serverid}', '${sdata.global_serverid}','${sdata.color}');">leave</a>
                                <a class="btn btn-secondary col-4" onclick="server_leave('srcard_${sdata.global_serverid}', '${sdata.global_serverid}', '${sdata.color}');">back</a>
                            </div>
                            <div class="card-norm">
                                <a class="btn btn-primary btn-connect disabled placeholder col-5" href='/user?serverid=${sdata.global_serverid}' style="background-color:${sdata.color};border-color:${sdata.color}"></a>
                                <a class="btn btn-secondary btn-sett disabled col-4" onclick="server_leave('srcard_${sdata.global_serverid}','${sdata.global_serverid}','${sdata.color}');">leave</a>
                            </div>
                        </div>
                    </div>
                `;
            });
            response.admin.forEach(sdata => {
                $('#cardHolderAdminServers')[0].innerHTML += `
                    <div class="card server_card o_server_card" aria-hidden="true" style="border-color:${sdata.color}" id="srcard_${sdata.global_serverid}">
                        <div class="card-body" style="min-width: 20rem;">
                            <h5 class="card-title">
                                <span class="col-6">${sdata.nickname}</span>
                            </h5>
                            <p class="card-text placeholder-glow">
                                <span class="placeholder col-7"></span>
                            </p>
                            <div class="card-options"></div>
                            <div class="card-settings d-none">
                                <a class="btn btn-primary col-4" onclick="server_sett('srcard_${sdata.global_serverid}', '${sdata.global_serverid}', '${sdata.color}',true);" style="background-color:${sdata.color};border-color:${sdata.color}">save</a>
                                <a class="btn btn-secondary col-4" onclick="server_sett('srcard_${sdata.global_serverid}', '${sdata.global_serverid}', '${sdata.color}');">close</a>
                            </div>
                            <div class="card-norm">
                                <a class="btn btn-primary btn-connect disabled placeholder col-5" href='/server?serverid=${sdata.global_serverid}' style="background-color:${sdata.color};border-color:${sdata.color}"></a>
                                <a class="btn btn-secondary btn-sett disabled col-4" onclick="server_sett('srcard_${sdata.global_serverid}', '${sdata.global_serverid}', '${sdata.color}');">settings</a>
                            </div>
                        </div>
                    </div>
                `;
            });
            response.offline.forEach(sdata => {
                $('#cardHolderNonAvialableServers')[0].innerHTML += `
                    <div class="card server_card" aria-hidden="true" style="border-color:${sdata.color}" id="srcard_${sdata.global_serverid}">
                        <div class="card-body" style="min-width: 20rem;">
                            <h5 class="card-title">
                                <span class="col-6">${sdata.nickname}</span>
                            </h5>
                            <p class="card-text">
                                <p>cant connect - server is offline :(</p>
                            </p>
                            <a class="btn btn-primary disabled placeholder col-6" aria-disabled="true" style="background-color:${sdata.color};border-color:${sdata.color}"></a>
                        </div>
                    </div>
                `;
            });

        },
        error: function(xhr, status, error) {
            console.error('Error:', xhr.responseText);
            $('#cardHolderAvialableServers')[0].innerHTML = 'Error happened whilest getting the servers. Please try again later.'
            return;
        }
    });

    await $('.o_server_card').each(function() {
        let serverCard = this;
        $.ajax({
            url: '/_api/clog/get_status',
            type: 'POST',
            data: JSON.stringify({'serverid':this.id.split('_')[1]}),
            contentType: 'application/json; charset=UTF-8',
            success: function(response) {
                if(response){
                    $(serverCard).find('.card-text')[0].innerText = 'ready to connect!';
                    $(serverCard).find('.btn-connect')[0].classList.remove('disabled');
                    $(serverCard).find('.btn-sett')[0].classList.remove('disabled');
                    $(serverCard).find('.btn-connect')[0].classList.remove('placeholder');
                    $(serverCard).find('.btn-connect')[0].innerText = 'connect';
                }else{
                    $(serverCard).find('.card-text')[0].innerText = 'cant reach server, maybe its offline!?';
                    $(serverCard).find('.btn-sett')[0].classList.remove('disabled');
                }
            }
        })
    });
}

// firstLoad();
$(document).ready(function() {
    sleep(1000).then(() => {main();});
});
