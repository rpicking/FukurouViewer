import QtQuick 2.0

Component {
    DraggableItem {
        Rectangle {
            height: 80
            width: _listView.width
            //color: "white"

            Text {
                id: nameField
                text: model.name
                anchors.top: parent.top
                anchors.topMargin: 10
                font.pointSize: 16
                anchors.left: parent.left
                anchors.leftMargin: 10
            }

            Text {
                id: pathField
                text: model.path
                font.pointSize: 8
                font.italic: true
                anchors.top: nameField.bottom
                anchors.topMargin: 15
                anchors.left: nameField.left
                anchors.leftMargin: 20
            }

            Rectangle {
                id: colorBox
                width: height
                color: model.color
                border.width: 1
                anchors.top: parent.top
                anchors.topMargin: 10
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 10
                anchors.right: parent.right
                anchors.rightMargin: 5
            }

            // Bottom line separator
            Rectangle {
                anchors {
                    left: parent.left
                    right: parent.right
                    bottom: parent.bottom
                }
                height: 1
                color: "lightgrey"
            }
        }

        draggedItemParent: _listView

        onMoveItemRequested: {
            _listView.model.move(from, to, 1);
            var items = [];

            for(var i = 0; i < _listView.model.count; ++i) {
                //console.log(_listView.model.get(i).name);
                items.push({ "id": _listView.model.get(i).id,
                               "order": i + 1 });
            }
            mainWindow.updateFolders(items)
        }
    }
}
