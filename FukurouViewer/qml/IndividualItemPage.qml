import QtQuick 2.0
import QtQuick.Controls 2.5
import QtMultimedia 5.13

Item {
    property string source: ""
    property string type: ""

    Component.onCompleted: {
        loadSource();
        forceActiveFocus();
    }

    Component.onDestruction: {
        mediaPlayer.stop();
    }

    onActiveFocusChanged: {
        if (!activeFocus) return;

        if (type === "video") {
            videoOutput.forceActiveFocus();
        } else {
            image.forceActiveFocus();
        }
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
    }

    function setVideo(videoSource) {
        mediaPlayer.source = videoSource;
        videoOutput.visible = true;
    }

    function togglePlayback() {
        if (mediaPlayer.playbackState == MediaPlayer.PlayingState) {
            mediaPlayer.pause();
        } else {
            mediaPlayer.play();
        }
    }

    function seekForward() {
        mediaPlayer.seek(mediaPlayer.position + 5000);
    }

    function seekBackward() {
        mediaPlayer.seek(mediaPlayer.position - 5000)
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

        Keys.onSpacePressed: togglePlayback();
        Keys.onLeftPressed: seekBackward();
        Keys.onRightPressed: seekForward();
    }

    MouseArea {
        id: playArea

        x: videoOutput.contentRect.x
        y: videoOutput.contentRect.y
        width: videoOutput.contentRect.width
        height: videoOutput.contentRect.height

        acceptedButtons: Qt.AllButtons
        propagateComposedEvents: true
        onClicked: {
            switch(mouse.button) {
                case Qt.LeftButton:
                    if (type === "video") togglePlayback();
                    break;
                case Qt.BackButton:
                    if (type === "video") {
                        seekBackward();
                    } else {
                        mouse.accepted = false;
                    }
                    break;
                case Qt.ForwardButton:
                    seekForward();
                    break;
            }
        }
    }
}
