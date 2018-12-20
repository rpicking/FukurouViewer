import QtQuick 2.11
//import QtQuick.Dialogs 1.2
import QtQuick.Controls 2.1

import QtQuick.Controls 1.4 as Old
import QtQuick.Controls.Styles 1.4 as OldStyle

import "."

Old.ScrollView {
    id: scrollView

    GridView {
        id: grid
        property int viewportWidth: parent.width
        property int columns: viewportWidth / 220
        cellWidth: Math.floor(viewportWidth / columns)
        cellHeight: 300
        model: gridModel
        interactive: true
        boundsBehavior: Flickable.StopAtBounds
        cacheBuffer: (350 + 16) * 10

        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
        }
        delegate: Component {
            Loader {
                sourceComponent: Component {
                    Item {
                        width: grid.cellWidth
                        height: grid.cellHeight

                        BusyIndicator {
                            anchors.centerIn: parent
                            running: picture.status != Image.Ready
                        }

                        Rectangle {
                            anchors.fill: picture
                            color: "white"
                        }
                        Image {
                            id: picture
                            //width: 200
                            //height: 280
                            sourceSize.width: 200
                            sourceSize.height: 280
                            //asynchronous: true
                            fillMode: Image.PreserveAspectFit
                            source: "image://thumbs/" + encodeURIComponent(filepath)
                            anchors.centerIn: parent
                            smooth: false
                            onStateChanged: {
                                if (status == Image.Ready) {
                                    smooth = true;
                                }
                            }

                            states: [
                                State { name: 'loaded'; when: picture.status == Image.Ready }
                            ]

                            MouseArea {
                                pressAndHoldInterval: 250
                                onPressAndHold: {
                                    var xPercent = mouse.x / parent.width
                                    var yPercent = mouse.y / parent.height
                                    testImage.source = "file:///" + filepath

                                    var globalCoords = mapToGlobal(mouse.x, mouse.y);
                                    testPopup.openOnPoint(globalCoords, parent.width, parent.height, xPercent, yPercent);

                                    testPopup.show();
                                    testPopup.requestActivate();
                                }

                                anchors.fill: parent
                            }
                        }
                    }
                }
                asynchronous: index >= 60
            }
        }
    }
}
