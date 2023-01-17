function userSearch(search_keyword, socket) {
    var search_data = {"keyword": search_keyword};
    socket.send(JSON.stringify(search_data));

    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        if (data['event'] === 'search-result') {
            var str = '';
            data['users'].forEach(function (item) {

                str += '<div class="user-class card bg-light mb-3 col-6"> <div class="card-header">' +
                    item['phone_number'] +
                    '</div> <div class="card-body"> <h5 class="card-title">' +
                    item['username'] +
                    '</h5> </div> </div>'

            });
            $('#direct-creation #user-search-result').html(str);
        }
    };
}


$(document).ready(function () {

    var direct_member = null;


    const user_search_socket = new WebSocket(
        'ws://' + window.location.host + '/ws/user/search/'
    );

    const chatroom_creation_socket = new WebSocket(
        'ws://' + window.location.host + '/ws/chatroom/create/'
    )

    chatroom_creation_socket.onmessage = function (e) {
        var data = JSON.parse(e.data);
        alert(data['event'] + ': ' + data['description']);
    }

    $('#room-type').change(function () {
        let chat_type = $('#room-type option:selected').text();
        if (chat_type === 'Channel') {
            $('#direct-creation').attr("hidden", true);
            $('#group-creation').attr("hidden", true);
            $('#channel-creation').attr("hidden", false);
        }
        if (chat_type === 'Group') {
            $('#direct-creation').attr("hidden", true);
            $('#group-creation').attr("hidden", false);
            $('#channel-creation').attr("hidden", true);
        }
        if (chat_type === 'Direct') {
            $('#direct-creation').attr("hidden", false);
            $('#group-creation').attr("hidden", true);
            $('#channel-creation').attr("hidden", true);
        }
    });

    $('#direct-creation #user-search-submit').click(function () {
        var data = $(this).parent().find("input").val();
        userSearch(data, user_search_socket);
    });

    $('#direct-creation').on('click', '.user-class', function () {
        var data = $(this).find('.card-header').text();


        if ($(this).hasClass('bg-light')) {
            $(this).parent().find('.bg-success').addClass('bg-light')
            $(this).parent().find('.bg-success').removeClass('text-white bg-success');
            $(this).addClass('bg-success');
            $(this).addClass('text-white');
            $(this).removeClass('bg-light');
            direct_member = data;
        } else {
            $(this).removeClass('bg-success');
            $(this).removeClass('text-white');
            $(this).addClass('bg-light');

            direct_member = null;
        }
    });

    $('#create-direct').click(function () {
        if (!direct_member)
            alert("Please select a user");
        else {
            var data = {'chatroom_type': 'direct', 'phone_number': direct_member};
            chatroom_creation_socket.send(JSON.stringify(data))
        }
    });

    $('#create-group').click(function () {
        var group_name = $('#group-name').val();

        alert(group_name);

        if (!group_name)
            alert("Please choose a name for your group");
        else {
            var data = {'chatroom_type': 'group', 'group_name': group_name};
            chatroom_creation_socket.send(JSON.stringify(data))
        }
    });


    $('#create-channel').click(function () {
        var channel_name = $('#channel-name').val();

        alert(channel_name);

        if (!channel_name)
            alert("Please choose a name for your channel");
        else {
            var data = {'chatroom_type': 'channel', 'channel_name': channel_name};
            chatroom_creation_socket.send(JSON.stringify(data))
        }
    });

})