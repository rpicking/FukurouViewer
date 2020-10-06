import QtQuick 2.15
import QtQuick.Controls 2.15

import QtQuick.Controls 1.4 as Old

import "."

Old.ScrollView {
    id: galleryRoot
    property var usedModel: undefined
    property double imageWidth: 200
    property double imageHeight: 280
    property double columnSpacing: 20
    property double rowSpacing: 20

    Item {
        id: gridContainer
        width: galleryRoot.viewport.width
        height: grid.contentHeight + columnSpacing

        GridView {
            id: grid
            property int columns: width / imageWidth
            property double horizontalSpacing: columnSpacing / 2
            property double verticalSpacing: rowSpacing / 2

            height: contentHeight
            cellWidth: Math.floor(width / columns)
            cellHeight: imageHeight + verticalSpacing

            model: usedModel
            interactive: true
            boundsBehavior: Flickable.StopAtBounds
            cacheBuffer: 50 // cellHeight * 4 // (350 + 16) * 10

            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                leftMargin: horizontalSpacing
                rightMargin: horizontalSpacing
                topMargin: verticalSpacing
            }

            delegate: Loader {
                    sourceComponent: Component {
                        Item {
                            id: rootItemBackground
                            width: grid.cellWidth
                            height: grid.cellHeight

                            Item {
                                id: rootItem

                                anchors {
                                    fill: parent
                                    topMargin: grid.verticalSpacing
                                    bottomMargin: grid.verticalSpacing
                                    leftMargin: grid.horizontalSpacing
                                    rightMargin: grid.horizontalSpacing
                                }

                                BusyIndicator {
                                    anchors.centerIn: parent
                                    running: picture.status != Image.Ready
                                }

                                Image {
                                    id: picture
                                    //width: 200
                                    //height: 280
                                    sourceSize.width: imageWidth
                                    sourceSize.height: imageHeight
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
                                            var xPercent = mouse.x / parent.width;
                                            var yPercent = mouse.y / parent.height;

                                            blowUpWindow.setSource("file:///" + filepath);

                                            var globalCoords = mapToGlobal(mouse.x, mouse.y);
                                            blowUpWindow.openOnPoint(globalCoords, parent.width, parent.height, xPercent, yPercent);

                                            blowUpWindow.show();
                                            blowUpWindow.requestActivate();
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
                    }
                    //asynchronous: index >= 30
                }
        }
    }
}
