using System.Diagnostics;
using System.Net.Http;

const string Url = "http://127.0.0.1:8000/";

var baseDir = AppContext.BaseDirectory;
var pythonPath = Path.Combine(baseDir, "runtime", "python.exe");
var appPath = Path.Combine(baseDir, "app.py");

try
{
    if (!await IsRunning())
    {
        if (!File.Exists(pythonPath))
        {
            ShowMessage("未找到内置 Python 运行环境：runtime\\python.exe");
            return;
        }

        if (!File.Exists(appPath))
        {
            ShowMessage("未找到应用文件：app.py");
            return;
        }

        var startInfo = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = "\"app.py\"",
            WorkingDirectory = baseDir,
            UseShellExecute = false,
            CreateNoWindow = true,
            WindowStyle = ProcessWindowStyle.Hidden,
        };

        Process.Start(startInfo);
        await WaitUntilReady();
    }

    Process.Start(new ProcessStartInfo
    {
        FileName = Url,
        UseShellExecute = true,
    });
}
catch (Exception ex)
{
    ShowMessage("启动失败：" + ex.Message);
}

static async Task<bool> IsRunning()
{
    try
    {
        using var client = new HttpClient { Timeout = TimeSpan.FromMilliseconds(800) };
        var response = await client.GetAsync(Url + "api/health");
        return response.IsSuccessStatusCode;
    }
    catch
    {
        return false;
    }
}

static async Task WaitUntilReady()
{
    for (var i = 0; i < 20; i++)
    {
        if (await IsRunning())
        {
            return;
        }
        await Task.Delay(300);
    }

    throw new TimeoutException("服务启动超时，请确认 8000 端口没有被其他程序占用。");
}

static void ShowMessage(string message)
{
    var escaped = message.Replace("'", "''");
    Process.Start(new ProcessStartInfo
    {
        FileName = "powershell",
        Arguments = $"-NoProfile -Command \"Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('{escaped}', '长沙中考录取预测系统')\"",
        UseShellExecute = false,
        CreateNoWindow = true,
    });
}
