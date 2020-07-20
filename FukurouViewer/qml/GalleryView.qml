import QtQuick 2.11
//import QtQuick.Dialogs 1.2
import QtQuick.Controls 2.1

import QtQuick.Controls 1.4 as Old
import QtQuick.Controls.Styles 1.4 as OldStyle

import "."

Old.ScrollView {
    id: scrollView

    property var usedModel: undefined

    GridView {
        id: grid
        property int viewportWidth: parent.width
        property int columns: viewportWidth / 220
        property double horizontalSpacing: 10
        property double verticalSpacing: 10
        cellWidth: Math.floor(viewportWidth / columns)
        cellHeight: 300

        model: usedModel
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
                        id: rootItem
                        width: grid.cellWidth - grid.horizontalSpacing
                        height: grid.cellHeight - grid.verticalSpacing

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
                            source: "image://thumbs/" + encodeURIComponent(fileURI)
                            anchors {
                                top: rootItem.top
                                right: rootItem.right
                                bottom: nameText.top
                                left: rootItem.left
                            }
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
                                onDoubleClicked: {
                                    stack.push(Qt.resolvedUrl("IndividualItemPage.qml"), { filepath: filepath, type: type } );
                                }
                                onPressAndHold: {
                                    var xPercent = mouse.x / parent.width
                                    var yPercent = mouse.y / parent.height

                                    testPopup.setSource("file:///" + filepath)

                                    var globalCoords = mapToGlobal(mouse.x, mouse.y);
                                    testPopup.openOnPoint(globalCoords, parent.width, parent.height, xPercent, yPercent);

                                    testPopup.show();
                                    testPopup.requestActivate();
                                }

                                anchors.fill: parent
                            }
                        }

                        Text {
                            id: nameText
                            text: name
                            height: 40
                            font.pointSize: 10
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.Wrap
                            padding: {
                                top: 2
                                bottom: 2
                            }
                            anchors {
                                bottom: parent.bottom
                                left: parent.left
                                right: parent.right
                            }
                        }
                    }
                }
                asynchronous: index >= 30
            }
        }
    }
}
