import QtQuick 2.11
import QtMultimedia 5.13

Item {

    anchors.fill: parent

    function setFileSource(videoSource, type) {
        mediaPlayer.source = "file:///" + videoSource;
    }

    Component.onDestruction: {
        mediaPlayer.stop();
    }

    onActiveFocusChanged: {
        if (!activeFocus) return;
        videoOutput.forceActiveFocus();
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

    MediaPlayer {
        id: mediaPlayer
        loops: MediaPlayer.Infinite;
        autoPlay: true
    }

    VideoOutput {
        id: videoOutput
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
                    togglePlayback();
                    break;
                case Qt.BackButton:
                    seekBackward();
                    break;
                case Qt.ForwardButton:
                    seekForward();
                    break;
            }
        }
    }
}
