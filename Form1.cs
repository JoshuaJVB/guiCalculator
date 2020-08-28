using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace csharpGuiCalc
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void btnCopy_Click(object sender, EventArgs e)
        {
            Clipboard.SetText(display.Text);
        }

        private void btnClearEverything_Click(object sender, EventArgs e)
        {
            previousOperation = Operation.None;
            display.Clear();
        }

        private void btnClear_Click(object sender, EventArgs e)
        {
            if (display.Text.Length > 0)
            {
                double d;
                if(double.TryParse(display.Text[display.Text.Length - 1].ToString(), out d))
                {
                    previousOperation = Operation.None;
                }

                display.Text = display.Text.Remove(display.Text.Length - 1, 1);
            }
        }

        private void btnDiv_Click(object sender, EventArgs e)
        {
            if (previousOperation != Operation.None)
                PerformCalculation(previousOperation);

            previousOperation = Operation.Div;
            display.Text += (sender as Button).Text;

        }

        private void btnMul_Click(object sender, EventArgs e)
        {
            if (previousOperation != Operation.None)
                PerformCalculation(previousOperation);

            previousOperation = Operation.Mul;
            display.Text += (sender as Button).Text;
        }

        private void btnMin_Click(object sender, EventArgs e)
        {
            if (previousOperation != Operation.None)
                PerformCalculation(previousOperation);

            previousOperation = Operation.Sub;
            display.Text += (sender as Button).Text;
        }

        private void btnPlus_Click(object sender, EventArgs e)
        {
            if (previousOperation != Operation.None)
                PerformCalculation(previousOperation);

            previousOperation = Operation.Plus;
            display.Text += (sender as Button).Text;
        }

        private void PerformCalculation(Operation previousOperation)
        {
            List<double> lstNums = new List<double>();
            switch (previousOperation)
            {
                case Operation.Plus:
                    lstNums = display.Text.Split('+').Select(double.Parse).ToList();
                    display.Text = (lstNums[0] + lstNums[1]).ToString();
                    break;
                case Operation.Sub:
                    lstNums = display.Text.Split('-').Select(double.Parse).ToList();
                    display.Text = (lstNums[0] - lstNums[1]).ToString();
                    break;
                case Operation.Mul:
                    lstNums = display.Text.Split('*').Select(double.Parse).ToList();
                    display.Text = (lstNums[0] * lstNums[1]).ToString();
                    break;
                case Operation.Div:
                    try
                    {
                        lstNums = display.Text.Split('/').Select(double.Parse).ToList();
                        display.Text = (lstNums[0] / lstNums[1]).ToString();
                    }
                    catch (DivideByZeroException)
                    {
                        display.Text = "EEEEEEEE";
                    }
                    break;
                default:
                    break;
            }
        }

        private void btnEq_Click(object sender, EventArgs e)
        {
            if (previousOperation == Operation.None)
                return;
            else
                PerformCalculation(previousOperation);
        }

        private void btnNum_Click(object btn, EventArgs e)
        {
            display.Text += (btn as Button).Text;
        }

        enum Operation
        {
            Plus,
            Sub,
            Mul,
            Div,
            None
        }
        static Operation previousOperation = Operation.None;
    }
}
