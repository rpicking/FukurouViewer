import QtQuick 2.0
import QtQuick.Controls 2.5
import QtMultimedia 5.13

Page {
    property string source: ""
    property string type: ""

    Component.onCompleted: {
        console.log(type);
        loadSource();
    }

    Component.onDestruction: {
        mediaPlayer.stop();
    }

    function loadSource() {
        closeTypes();

        switch (type) {
        case "image":
            setImage(source);
            break;
        case "video":
            setVideo(source);
            break;
        default:
            console.log("other type for file: " + source)
            break;
        }
    }

    // hides all types of players/viewers possible and clears their source
    function closeTypes() {
        image.visible = false;
        image.source = "";

        mediaPlayer.stop();
        videoOutput.visible = false;
        mediaPlayer.source = "";
    }

    function setImage(imageSource) {
        image.source = imageSource;
        image.visible = true;
        image.forceActiveFocus();
    }

    function setVideo(videoSource) {
        mediaPlayer.source = videoSource;
        videoOutput.visible = true;
        videoOutput.forceActiveFocus();
    }

    AnimatedImage {
        id: image
        visible: false
        fillMode: Image.PreserveAspectFit
        smooth: true
        anchors {
            fill: parent
        }
    }

    MediaPlayer {
        id: mediaPlayer
        loops: MediaPlayer.Infinite;
        autoPlay: true
    }

    VideoOutput {
        id: videoOutput
        visible: false
        source: mediaPlayer
        fillMode: VideoOutput.PreserveAspectFit
        anchors.fill: parent
        Keys.onSpacePressed: mediaPlayer.playbackState == MediaPlayer.PlayingState ? mediaPlayer.pause() : mediaPlayer.play();
        Keys.onLeftPressed: seekBackward();
        Keys.onRightPressed: seekForward();

        function seekForward() {
            mediaPlayer.seek(mediaPlayer.position + 5000);
        }

        function seekBackward() {
            mediaPlayer.seek(mediaPlayer.position - 5000)
        }
    }

    MouseArea {
        id: playArea
        acceptedButtons: Qt.AllButtons
        anchors.fill: parent
        propagateComposedEvents: true
        onClicked: {
            switch(mouse.button) {
                case Qt.LeftButton:
                    if (type === "video") mediaPlayer.play();
                    break;
                case Qt.BackButton:
                    if (type === "video") {
                        videoOutput.seekBackward();
                    } else {
                        mouse.accepted = false;
                    }
                    break;
                case Qt.ForwardButton:
                    videoOutput.seekForward();
                    break;
            }
        }
    }

//    Video {
//        id: video
//        visible: false
//        fillMode: VideoOutput.PreserveAspectFit
//        loops: MediaPlayer.Infinite
//        autoPlay: true;
//        anchors {
//            fill: parent
//        }

//        MouseArea {
//            anchors.fill: parent
//            onClicked: {
//                video.play()
//            }
//            Keys.onPressed: {
//                console.log(event.key);
//            }
//        }

//        Keys.onSpacePressed: video.playbackState == MediaPlayer.PlayingState ? video.pause() : video.play()
//        Keys.onLeftPressed: video.seek(video.position - 5000)
//        Keys.onRightPressed: video.seek(video.position + 5000)
//    }
}
