using ExxerciseAbstractMethods.Entities;

namespace ExxerciseAbstractMethods
{
    class Program
    {
        static void Main(string[] args)
        {
            /*
            string name = "Alex";
            double anual = 120000.00;
            double health = 1000.00;

            Individual payer = new Individual(name, anual, health);

            Console.WriteLine(payer.Name + ": $ " + payer.Tax());
            */
            /*
            string name = "MicroBlob";
            double anual = 400000.00;
            int employees = 25;

            Company payer = new Company(name, anual, employees);

            Console.WriteLine(payer.Name + ": $ " + payer.Tax().ToString("F2"));
            */
            List<TaxPayer> list = new List<TaxPayer>();

            Console.Write("Enter the name of tax payers: ");
            int n = int.Parse(Console.ReadLine());

            for (int i = 1; i <= n; i++)
            {
                Console.WriteLine($"Tax payer #{i} data:");
                Console.Write("Individual or company (i/c)? ");
                char ch = char.Parse(Console.ReadLine());
                Console.Write("Name: ");
                string name = Console.ReadLine();
                Console.Write("Anual income: ");
                double anual = double.Parse(Console.ReadLine());

                if (ch == 'i')
                {
                    Console.Write("Health expenditures: ");
                    double health = double.Parse(Console.ReadLine());
                    list.Add(new Individual(name, anual, health));
                }
                else if (ch == 'c')
                {
                    Console.Write("Number of employees: ");
                    int employees = int.Parse(Console.ReadLine());
                    list.Add(new Company(name, anual, employees));
                }
                else
                {
                    Console.WriteLine();
                    Console.WriteLine("bruh");
                }
            }

            Console.WriteLine();
            Console.WriteLine("TOTAL PAID:");
            double total = 0;
            foreach (TaxPayer tp in list)
            {
                Console.WriteLine(tp.Name + ": $ " + tp.Tax().ToString("F2"));
                Console.WriteLine(tp.Name + ": $ " + tp.Tax().ToString("F2"));

            }

            Console.WriteLine();
            Console.Write("TOTAL TAXES : $" + total.ToString("F2"));
        }
    }
}