#include <opencv2/opencv.hpp>
#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <QtWidgets/QApplication>
#include <QtWidgets/QWidget>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QFileDialog>
#include <QtWidgets/QTextEdit>
#include <QtWidgets/QMessageBox>

// Global variables
std::vector<cv::Point> clicked_points;
std::vector<cv::Point> rect_points;
std::vector<cv::Rect> rectangles;
int point_count = 0;
int rect_count = 0;
cv::Mat img;
cv::Mat img_backup;
std::map<std::string, std::string> PATHS;
std::vector<std::string> roomList;
int helperpath_counter = 1;
int current_helperpath = 1;
std::string last_action;  // Track the last action
std::vector<cv::Point> clicked_points;
cv::Mat img;



// Global variables
cv::Mat output_text_widget; // Similar to a text widget in Python, but in C++ we might use a GUI library (Qt, etc.) for actual GUI text display

// Function to map coordinates to a range of 0 to 120
int map_to_120(int value, int max_value) {
    return static_cast<int>((static_cast<float>(value) / max_value) * 248 - 124);
}

// Function to draw a grid on the image with specified number of cells
void draw_grid(cv::Mat& image) {
    int num_cells = 40;
    int height = image.rows;
    int width = image.cols;
    
    // Calculate the size of each cell
    float cell_width = static_cast<float>(width) / num_cells;
    float cell_height = static_cast<float>(height) / num_cells;

    // Draw vertical lines
    for (int i = 0; i <= num_cells; ++i) {
        int x = static_cast<int>(i * cell_width);
        cv::line(image, cv::Point(x, 0), cv::Point(x, height), cv::Scalar(150, 130, 10), 1); // Vertical lines
    }

    // Draw horizontal lines
    for (int i = 0; i <= num_cells; ++i) {
        int y = static_cast<int>(i * cell_height);
        cv::line(image, cv::Point(0, y), cv::Point(width, y), cv::Scalar(150, 130, 10), 1); // Horizontal lines
    }
}

// Function to draw connections (lines between all consecutive points)
void draw_connections() {
    // Iterate through the clicked points and draw lines between consecutive points
    for (size_t i = 0; i < clicked_points.size() - 1; ++i) {
        cv::line(img, clicked_points[i], clicked_points[i + 1], cv::Scalar(0, 255, 0), 2);  // Green lines with thickness of 2
    }
}

// Function to check if two points are near each other
bool near(int x1, int y1, int x2, int y2) {
    const int dist = 3;
    if (std::abs(x1 - x2) < dist && std::abs(y1 - y2) < dist) {
        return true;  // Points are near
    }
    return false;  // Points are not near
}


int selected_id = -1;


// // Function for handling mouse click events
// void click_event(int event, int x, int y, int flags, void* param) {
//     if (event == cv::EVENT_LBUTTONDOWN) {  // Left click event
//         if (cv::waitKey(0) == 17) {  // Check if Ctrl key is pressed (17 = 'ctrl' key)
//             if (selected_id != -1) {
//                 // Update the selected point with new coordinates
//                 clicked_points[selected_id] = cv::Point(x, y);
//                 int height = img.rows;
//                 int width = img.cols;
//                 int new_x_mapped = map_to_120(x, width);
//                 int new_y_mapped = map_to_120(y, height);
//                 PATHS[current_helperpath][selected_id] = {new_x_mapped, new_y_mapped};

//                 // Print updated coordinates (in the console for now)
//                 std::cout << "Moved point " << selected_id + 1 << " to: (" << new_x_mapped << ", " << new_y_mapped << ")" << std::endl;

//                 // Redraw image
//                 img = img_backup.clone();
//                 draw_grid(img);

//                 // Re-draw all points with updated numbers
//                 for (size_t i = 0; i < clicked_points.size(); ++i) {
//                     cv::putText(img, std::to_string(i + 1), clicked_points[i], cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 255, 255), 2);
//                     cv::circle(img, clicked_points[i], 4, cv::Scalar(0, 255, 0), -1);
//                 }

//                 // Draw all rectangles again
//                 for (const auto& rect : rectangles) {
//                     cv::rectangle(img, rect.first, rect.second, cv::Scalar(255, 0, 0), 2);
//                     int center_x = (rect.first.x + rect.second.x) / 2;
//                     int center_y = (rect.first.y + rect.second.y) / 2;
//                     cv::putText(img, "Rect " + std::to_string(&rect - &rectangles[0] + 1), cv::Point(center_x, center_y), cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 0, 0), 2);
//                 }

//                 // Draw connections
//                 draw_connections();
//                 cv::imshow("Image", img);

//                 // Deselect point after moving
//                 selected_id = -1;
//             } else {
//                 // Find point to select
//                 for (size_t i = 0; i < PATHS[current_helperpath].size(); ++i) {
//                     auto point = PATHS[current_helperpath][i];
//                     if (near(point.first, point.second, x, y)) {
//                         selected_id = i;
//                         break;
//                     }
//                 }

//                 if (selected_id != -1) {
//                     std::cout << "Point selected for movement: " << selected_id << std::endl;
//                 }
//             }
//         }
//         else if (cv::waitKey(0) == 18) {  // Check if Alt key is pressed (18 = 'alt' key)
//             // Find point to remove
//             for (size_t i = 0; i < PATHS[current_helperpath].size(); ++i) {
//                 auto point = PATHS[current_helperpath][i];
//                 if (near(point.first, point.second, x, y)) {
//                     // Remove the point
//                     clicked_points.erase(clicked_points.begin() + i);
//                     PATHS[current_helperpath].erase(PATHS[current_helperpath].begin() + i);

//                     std::cout << "Removed point " << i + 1 << std::endl;

//                     // Redraw image
//                     img = img_backup.clone();
//                     draw_grid(img);

//                     // Redraw remaining points
//                     for (size_t j = 0; j < clicked_points.size(); ++j) {
//                         cv::putText(img, std::to_string(j + 1), clicked_points[j], cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 255, 255), 2);
//                         cv::circle(img, clicked_points[j], 4, cv::Scalar(0, 255, 0), -1);
//                     }

//                     // Draw connections
//                     draw_connections();
//                     cv::imshow("Image", img);
//                     break;
//                 }
//             }
//         } else {
//             // Regular left-click behavior (add a new point)
//             clicked_points.push_back(cv::Point(x, y));
//             point_count++;

//             int height = img.rows;
//             int width = img.cols;
//             int x_mapped = map_to_120(x, width);
//             int y_mapped = map_to_120(y, height);

//             // Update output in the text widget
//             std::cout << "Clicked point " << point_count << ": (" << x_mapped << ", " << y_mapped << ")" << std::endl;

//             if (PATHS.find(current_helperpath) == PATHS.end()) {
//                 PATHS[current_helperpath] = {};
//             }
//             PATHS[current_helperpath].push_back({x_mapped, y_mapped});

//             // Draw the new point and number
//             cv::putText(img, std::to_string(point_count), cv::Point(x, y), cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 255, 255), 2);
//             cv::circle(img, cv::Point(x, y), 4, cv::Scalar(0, 255, 0), -1);

//             // Draw connections
//             draw_connections();
//             cv::imshow("Image", img);
//         }
//     }
//     else if (event == cv::EVENT_RBUTTONDOWN) {  // Right click event for rectangles
//         if (rect_points.size() == 0) {
//             rect_points.push_back(cv::Point(x, y));
//         } else if (rect_points.size() == 1) {
//             rect_points.push_back(cv::Point(x, y));
//             int x1 = rect_points[0].x, y1 = rect_points[0].y;
//             int x2 = rect_points[1].x, y2 = rect_points[1].y;

//             if (x1 < x2 && y1 < y2) {
//                 rect_count++;
//                 cv::rectangle(img, cv::Point(x1, y1), cv::Point(x2, y2), cv::Scalar(255, 0, 0), 2);
//                 int center_x = (x1 + x2) / 2;
//                 int center_y = (y1 + y2) / 2;
//                 cv::putText(img, "Rect " + std::to_string(rect_count), cv::Point(center_x, center_y), cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 0, 0), 2);

//                 // Store the rectangle coordinates
//                 roomList.push_back({map_to_120(x1, img.cols), map_to_120(y1, img.rows), map_to_120(x2, img.cols), map_to_120(y2, img.rows), rect_count});

//                 // Store the rectangle points
//                 rectangles.push_back({cv::Point(x1, y1), cv::Point(x2, y2)});
//                 rect_points.clear();
//                 cv::imshow("Image", img);
//             } else {
//                 std::cout << "Invalid rectangle coordinates: Ensure x1 < x2 and y1 < y2." << std::endl;
//                 rect_points.clear();
//             }
//         }
//     }



// Function for handling mouse click events
void click_event(int event, int x, int y, int flags, void* param) {
    if (event == cv::EVENT_LBUTTONDOWN) {  // Left click event
        if (cv::waitKey(0) == 17) {  // Check if Ctrl key is pressed (17 = 'ctrl' key)
            if (selected_id != -1) {
                // Update the selected point with new coordinates
                clicked_points[selected_id] = cv::Point(x, y);
                int height = img.rows;
                int width = img.cols;
                int new_x_mapped = map_to_120(x, width);
                int new_y_mapped = map_to_120(y, height);
                PATHS[current_helperpath][selected_id] = {new_x_mapped, new_y_mapped};

                // Print updated coordinates (in the console for now)
                std::cout << "Moved point " << selected_id + 1 << " to: (" << new_x_mapped << ", " << new_y_mapped << ")" << std::endl;

                // Redraw image
                img = img_backup.clone();
                draw_grid(img);

                // Re-draw all points with updated numbers
                for (size_t i = 0; i < clicked_points.size(); ++i) {
                    cv::putText(img, std::to_string(i + 1), clicked_points[i], cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 255, 255), 2);
                    cv::circle(img, clicked_points[i], 4, cv::Scalar(0, 255, 0), -1);
                }

                // Draw all rectangles again
                for (const auto& rect : rectangles) {
                    cv::rectangle(img, rect.first, rect.second, cv::Scalar(255, 0, 0), 2);
                    int center_x = (rect.first.x + rect.second.x) / 2;
                    int center_y = (rect.first.y + rect.second.y) / 2;
                    cv::putText(img, "Rect " + std::to_string(&rect - &rectangles[0] + 1), cv::Point(center_x, center_y), cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 0, 0), 2);
                }

                // Draw connections
                draw_connections();
                cv::imshow("Image", img);

                // Deselect point after moving
                selected_id = -1;
            } else {
                // Find point to select
                for (size_t i = 0; i < PATHS[current_helperpath].size(); ++i) {
                    auto point = PATHS[current_helperpath][i];
                    if (near(point.first, point.second, x, y)) {
                        selected_id = i;
                        break;
                    }
                }

                if (selected_id != -1) {
                    std::cout << "Point selected for movement: " << selected_id << std::endl;
                }
            }
        }
        else if (cv::waitKey(0) == 18) {  // Check if Alt key is pressed (18 = 'alt' key)
            // Find point to remove
            for (size_t i = 0; i < PATHS[current_helperpath].size(); ++i) {
                auto point = PATHS[current_helperpath][i];
                if (near(point.first, point.second, x, y)) {
                    // Remove the point
                    clicked_points.erase(clicked_points.begin() + i);
                    PATHS[current_helperpath].erase(PATHS[current_helperpath].begin() + i);

                    std::cout << "Removed point " << i + 1 << std::endl;

                    // Redraw image
                    img = img_backup.clone();
                    draw_grid(img);

                    // Redraw remaining points
                    for (size_t j = 0; j < clicked_points.size(); ++j) {
                        cv::putText(img, std::to_string(j + 1), clicked_points[j], cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 255, 255), 2);
                        cv::circle(img, clicked_points[j], 4, cv::Scalar(0, 255, 0), -1);
                    }

                    // Draw connections
                    draw_connections();
                    cv::imshow("Image", img);
                    break;
                }
            }
        } else {
            // Regular left-click behavior (add a new point)
            clicked_points.push_back(cv::Point(x, y));
            point_count++;

            int height = img.rows;
            int width = img.cols;
            int x_mapped = map_to_120(x, width);
            int y_mapped = map_to_120(y, height);

            // Update output in the text widget
            std::cout << "Clicked point " << point_count << ": (" << x_mapped << ", " << y_mapped << ")" << std::endl;

            if (PATHS.find(current_helperpath) == PATHS.end()) {
                PATHS[current_helperpath] = {};
            }
            PATHS[current_helperpath].push_back({x_mapped, y_mapped});

            // Draw the new point and number
            cv::putText(img, std::to_string(point_count), cv::Point(x, y), cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 255, 255), 2);
            cv::circle(img, cv::Point(x, y), 4, cv::Scalar(0, 255, 0), -1);

            // Draw connections
            draw_connections();
            cv::imshow("Image", img);
        }
    }
    else if (event == cv::EVENT_RBUTTONDOWN) {  // Right click event for rectangles
        if (rect_points.size() == 0) {
            rect_points.push_back(cv::Point(x, y));
        } else if (rect_points.size() == 1) {
            rect_points.push_back(cv::Point(x, y));
            int x1 = rect_points[0].x, y1 = rect_points[0].y;
            int x2 = rect_points[1].x, y2 = rect_points[1].y;

            if (x1 < x2 && y1 < y2) {
                rect_count++;
                cv::rectangle(img, cv::Point(x1, y1), cv::Point(x2, y2), cv::Scalar(255, 0, 0), 2);
                int center_x = (x1 + x2) / 2;
                int center_y = (y1 + y2) / 2;
                cv::putText(img, "Rect " + std::to_string(rect_count), cv::Point(center_x, center_y), cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 0, 0), 2);

                // Store the rectangle coordinates
                roomList.push_back({map_to_120(x1, img.cols), map_to_120(y1, img.rows), map_to_120(x2, img.cols), map_to_120(y2, img.rows), rect_count});

                // Store the rectangle points
                rectangles.push_back({cv::Point(x1, y1), cv::Point(x2, y2)});
                rect_points.clear();
                cv::imshow("Image", img);
            } else {
                std::cout << "Invalid rectangle coordinates: Ensure x1 < x2 and y1 < y2." << std::endl;
                rect_points.clear();
            }
        }
    }
}

// GUI for uploading image and other functionalities
class ImageAnnotationApp : public QWidget {
    Q_OBJECT
public:
    ImageAnnotationApp() {
        // Set up UI components
        setWindowTitle("Image Annotation Tool");
        QVBoxLayout* mainLayout = new QVBoxLayout;

        // Frame for buttons
        QHBoxLayout* buttonLayout = new QHBoxLayout;
        
        // Upload Button
        QPushButton* uploadButton = new QPushButton("Upload Image");
        buttonLayout->addWidget(uploadButton);
        connect(uploadButton, &QPushButton::clicked, this, &ImageAnnotationApp::upload_image);

        // Submit Button
        QPushButton* submitButton = new QPushButton("Submit");
        buttonLayout->addWidget(submitButton);
        connect(submitButton, &QPushButton::clicked, this, &ImageAnnotationApp::submit);

        // Clear Points Button
        QPushButton* clearPointsButton = new QPushButton("Clear Points");
        buttonLayout->addWidget(clearPointsButton);
        connect(clearPointsButton, &QPushButton::clicked, this, &ImageAnnotationApp::clear_points);

        // Clear Rectangles Button
        QPushButton* clearRectanglesButton = new QPushButton("Clear Rectangles");
        buttonLayout->addWidget(clearRectanglesButton);
        connect(clearRectanglesButton, &QPushButton::clicked, this, &ImageAnnotationApp::clear_rectangles);

        // Undo Button
        QPushButton* undoButton = new QPushButton("Undo");
        undoButton->setEnabled(false);
        buttonLayout->addWidget(undoButton);
        connect(undoButton, &QPushButton::clicked, this, &ImageAnnotationApp::undo);

        mainLayout->addLayout(buttonLayout);

        // Output Text Widget
        outputTextWidget = new QTextEdit;
        outputTextWidget->setReadOnly(true);
        mainLayout->addWidget(outputTextWidget);

        setLayout(mainLayout);
    }

private slots:
    void upload_image() {
        QString filePath = QFileDialog::getOpenFileName(this, "Open Image File", "", "Images (*.png *.jpg *.bmp *.tiff)");
        if (filePath.isEmpty()) {
            return;
        }

        img = cv::imread(filePath.toStdString());  // Load the selected image
        if (img.empty()) {
            QMessageBox::critical(this, "Error", "Unable to load image.");
            return;
        }

        img_backup = img.clone();

        // Resize the image if it's too large
        int max_width = 1000;
        if (img.cols > max_width) {
            double ratio = static_cast<double>(max_width) / img.cols;
            int new_height = static_cast<int>(img.rows * ratio);
            cv::resize(img, img, cv::Size(max_width, new_height));
        }

        draw_grid(img);
        cv::imshow("Image", img);
        cv::setMouseCallback("Image", click_event);
    }

    void submit() {
        outputTextWidget->append("Submitting current points and rectangles...");
    }

    void clear_points() {
        clicked_points.clear();
        point_count = 0;
        img = img_backup.clone();
        draw_grid(img);
        cv::imshow("Image", img);
        undo_button_enabled = false;  // Disable undo
    }

    void clear_rectangles() {
        rectangles.clear();
        rect_count = 0;
        img = img_backup.clone();
        draw_grid(img);
        cv::imshow("Image", img);
    }

    void undo() {
        if (last_action == 1 && !clicked_points.empty()) {  // Last action was adding a point
            clicked_points.pop_back();
            point_count--;
        } else if (last_action == 2 && !rectangles.empty()) {  // Last action was adding a rectangle
            rectangles.pop_back();
            rect_count--;
        }

        img = img_backup.clone();
        draw_grid(img);

        for (size_t i = 0; i < clicked_points.size(); ++i) {
            cv::circle(img, clicked_points[i], 5, cv::Scalar(0, 255, 0), -1);
            cv::putText(img, std::to_string(i + 1), clicked_points[i], cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 255, 255), 2);
        }

        for (size_t i = 0; i < clicked_points.size() - 1; ++i) {
            cv::line(img, clicked_points[i], clicked_points[i + 1], cv::Scalar(0, 255, 0), 2);
        }

        for (const auto& rect : rectangles) {
            cv::rectangle(img, rect.first, rect.second, cv::Scalar(255, 0, 0), 2);
        }

        cv::imshow("Image", img);
        undo_button_enabled = clicked_points.empty() && rectangles.empty();  // Disable undo if no actions left
    }

private:
    QTextEdit* outputTextWidget;
};

// Main function
int main(int argc, char* argv[]) {
    QApplication app(argc, argv);

    ImageAnnotationApp window;
    window.show();

    return app.exec();
}