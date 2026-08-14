// Класс главного окна приложения.
class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    MainWindow();
    void openFile();
    void saveFile();
    void processImage();
signals:
    // Сигнал о завершении обработки изображения.
    void imageProcessed(const QString& path);
public slots:
    // Слот: обновить строку состояния.
    void updateStatus(const QString& text);
private:
    QString currentFile;
    QImage image;
    QLabel* statusBarLabel;
};

// Класс обработки изображений.
class ImageProcessor {
public:
    ImageProcessor();
    QImage filter(const QImage& img);
    QImage resize(const QImage& img, int w, int h);
    QImage grayscale(const QImage& img);
private:
    int quality;
};
